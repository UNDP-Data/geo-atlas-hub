import uuid
import yaml
from kubernetes import client, config, utils
import asyncio
from nicegui import ui
import textwrap
import logging
import functools
from insightshub.config import settings


logger = logging.getLogger(__name__)


def spawn_marimo_session(notebook_path: str, mode: str = "run", namespace: str = "marimo", user_email: str = None):
    repo_url = f'https://oauth2:{settings.nb_github_token}@github.com/{settings.nb_github_repo}'


    config.load_incluster_config()
    k8s_client = client.ApiClient()

    session_id = uuid.uuid4().hex[:8]
    resource_name = f"marimo-{mode}-{session_id}"
    session_hostname = f"{session_id}.undpgeohub.org"  # The new dynamic subdomain

    yaml_template = textwrap.dedent(f"""\
    ---
    apiVersion: batch/v1
    kind: Job
    metadata:
      name: placeholder-name
    spec:
      ttlSecondsAfterFinished: 120
      template:
        metadata:
          labels:
            app: marimo-worker
            session: placeholder-session
        spec:
          restartPolicy: Never
          volumes:
          - name: session-workspace
            emptyDir: {{}}
          initContainers:
          - name: fetch-notebooks
            image: alpine/git:latest
            command: ["/bin/sh", "-c"]
            # 1. Clone repo metadata only (--no-checkout --depth 1)
            # 2. Tell Git to only track the specific notebook_path
            # 3. Checkout that single file
            args: 
            - |
              rm -rf /workspace/* && \
              git clone --no-checkout --depth 1 {repo_url} /workspace && \
              cd /workspace && \
              git sparse-checkout set "{notebook_path}" && \
              git checkout
            volumeMounts:
            - name: session-workspace
              mountPath: /workspace
          containers:
          - name: marimo
            image: insights-hub:latest
            imagePullPolicy: IfNotPresent 
            command: []
            ports:
            - containerPort: 8080
            # Main resources for running/editing the notebook
            resources:
              requests:
                memory: "2Gi"
                cpu: "2000m"     # 2 CPU cores
              limits:
                memory: "8Gi"   # Adjust this based on your dataset sizes
                cpu: "4000m"    # 1 full CPU core
            volumeMounts:
            - name: session-workspace
              mountPath: /workspace
    ---
    apiVersion: v1
    kind: Service
    metadata:
      name: placeholder-name
    spec:
      selector:
        session: placeholder-session
      ports:
      - port: 80
        targetPort: 8080
    ---
    apiVersion: gateway.networking.k8s.io/v1
    kind: HTTPRoute
    metadata:
      name: placeholder-name
    spec:
      parentRefs:
      - name: cluster-gateway
        namespace: default
      hostnames:
      - placeholder-hostname
      rules:
      - matches:
        - path:
            type: PathPrefix
            value: /
        backendRefs:
        - name: placeholder-name
          port: 80
    """)

    manifests = list(yaml.safe_load_all(yaml_template))
    job_dict, svc_dict, route_dict = manifests

    # 1. Mutate the Job
    job_dict['metadata']['name'] = resource_name
    job_dict['spec']['template']['metadata']['labels']['session'] = session_id

    # Notice we removed the --base-url flag entirely because it now lives at the root (/)
    if mode == "edit":
        job_dict['spec']['template']['spec']['containers'][0]['command'] = [
            "marimo", "edit", f"/workspace/{notebook_path}",
            "--host", "0.0.0.0", "--port", "8080", "--headless", "--no-token"
        ]
        if user_email:
            job_dict['spec']['template']['spec']['containers'][0]['env'] = [
                {"name": "GIT_AUTHOR_EMAIL", "value": user_email},
                {"name": "GIT_AUTHOR_NAME", "value": user_email.split('@')[0]}
            ]
    else:
        job_dict['spec']['template']['spec']['containers'][0]['command'] = [
            "marimo", "run", f"/workspace/{notebook_path}",
            "--host", "0.0.0.0", "--port", "8080"
        ]

    # 2. Mutate the Service
    svc_dict['metadata']['name'] = resource_name
    svc_dict['spec']['selector']['session'] = session_id

    # 3. Mutate the HTTPRoute (Inject the dynamic subdomain)
    route_dict['metadata']['name'] = resource_name
    route_dict['spec']['hostnames'][0] = session_hostname
    route_dict['spec']['rules'][0]['backendRefs'][0]['name'] = resource_name

    # 4. Apply all resources
    custom_api = client.CustomObjectsApi(k8s_client)
    for manifest in manifests:
        if manifest['kind'] == 'HTTPRoute':
            custom_api.create_namespaced_custom_object(
                group="gateway.networking.k8s.io",
                version="v1",
                namespace=namespace,
                plural="httproutes",
                body=manifest
            )
        else:
            utils.create_from_dict(k8s_client, manifest, namespace=namespace)

    final_url = f"https://{session_hostname}"
    logger.info(f"Provisioned resources for {resource_name} at {final_url}")

    return session_id, final_url


def get_pod_status(session_id: str, namespace: str = "marimo") -> str:
    """Queries K8s for the pod matching the session_id and returns a human-readable status."""
    core_v1 = client.CoreV1Api()

    # Find the pod we just spawned
    pods = core_v1.list_namespaced_pod(namespace=namespace, label_selector=f"session={session_id}")

    if not pods.items:
        return "Creating container..."

    pod = pods.items[0]
    phase = pod.status.phase

    if phase == "Pending":
        return "Allocating node and pulling image..."

    elif phase == "Running":
        # A pod can be 'Running' but not yet 'Ready' to accept traffic
        for condition in pod.status.conditions or []:
            if condition.type == "Ready" and condition.status == "True":
                return "Ready"
        return "Starting Marimo server..."

    elif phase in ["Failed", "Unknown"]:
        return "Error"

    return "Initializing..."





async def handle_session_launch(notebook_path: str, mode: str, namespace:str = "marimo", user_email: str=None):



    # 1. Create a modal dialog that prevents the user from clicking elsewhere
    with ui.dialog().classes('backdrop-blur-sm').props('persistent') as dialog, ui.card().classes(
            'w-full max-w-md p-6'):
        ui.label(f"Preparing {mode.capitalize()} Session").classes('text-xl font-bold mb-6 text-gray-800')

        with ui.row().classes('items-center gap-4 mb-2'):
            spinner = ui.spinner('dots', size='lg', color='primary')
            status_label = ui.label("Provisioning Kubernetes resources...").classes('text-gray-600')

        close_btn = ui.button('Close', on_click=dialog.close).classes('mt-4 hidden')

    dialog.open()
    loop = asyncio.get_event_loop()

    try:
        # 2. Spawn the K8s resources
        # Bind the keyword arguments safely using partial
        spawn_task = functools.partial(
            spawn_marimo_session,
            notebook_path=notebook_path,
            mode=mode,

        )

        session_id, target_url = await loop.run_in_executor(None, spawn_task)

        # 3. Smart Polling Loop (Timeout after 60 seconds)
        max_retries = 60
        for _ in range(max_retries):
            await asyncio.sleep(1)  # Yield control back to the UI to keep the spinner animating

            # Ask K8s what the pod is doing
            status = await loop.run_in_executor(None, get_pod_status, session_id, namespace)

            if status == "Ready":
                status_label.set_text("Environment ready! Routing traffic...")
                spinner.classes('hidden')  # Hide spinner
                ui.icon('check_circle', color='green', size='lg')  # Show success icon

                # Give the Ingress Controller 1.5 seconds to register the new Service IP
                await asyncio.sleep(1.5)

                ui.navigate.to(target_url)
                return

            elif status == "Error":
                status_label.set_text("Container failed to start.")
                status_label.classes('text-red-500 font-bold')
                spinner.classes('hidden')
                close_btn.classes(remove='hidden')  # Allow user to close dialog
                return

            else:
                # Update the UI with the current K8s phase (e.g., "Allocating node...")
                status_label.set_text(status)

        # 4. Handle Timeout
        status_label.set_text("Timed out waiting for environment.")
        status_label.classes('text-red-500 font-bold')
        spinner.classes('hidden')
        close_btn.classes(remove='hidden')

    except Exception as e:
        # Catch unexpected K8s API errors (e.g., RBAC issues, syntax errors)
        status_label.set_text(f"API Error: {str(e)}")
        status_label.classes('text-red-500 font-bold text-xs')
        spinner.classes('hidden')
        close_btn.classes(remove='hidden')