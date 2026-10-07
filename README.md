# geo-insights-hub
A governed management server and orchestration plane for deploying, editing, and executing reactive Marimo analytical apps.


# Installation &/ setup

---



# Development

---
The Insights Hub is a complex piece of software integrating several state-of-the-art 
technologies like [Git](https://git-scm.com/), [Marimo](https://marimo.io/), [NiceGUI](https://nicegui.io/) and [FastAPI](https://fastapi.tiangolo.com/) all behind an [oauth2](https://oauth.net/2/) wall.

To facilitate developers experience a local KinD cluster capable to provide an adequate environment
has been created. For detailed instructions follow [depl/README.md](depl/README.md).

> [!IMPORTANT]
> Note the [depl/cluster](depl/cluster) folder contains two cluster manifest files that are 
> very similar except on detail. The  worker nodes in [dev-cluster.yaml](depl/cluster/dev-cluster.yaml)
> are mounting the [src](src) folder as a volume. This make it possible for deployments to 
> mount the volume at runtime so the deployments have access to the source folder.
> 

By configuring the uvicorn inside docker to watch and reload the very same folder it is possible to observe
changes in real time while the service is being deployed.

Following steps are required to enable this setup:

- [x] ensure the [dev-cluster.yaml](depl/cluster/dev-cluster.yaml) is used by the [create.sh](depl/cluster/create.sh) script
- [x] deploy the hub inside the cluster using the deployment script
    ```shell
    ./depl/insights/deploy.sh
    ```
- [x] ensure the insights.${BASE_DOMAIN} is set in /etc/hosts file and pointing towards the load balancer
    ```shell
       172.20.0.5 auth.undpgeohub.org  demo.undpgeohub.org insights.undpgeohub.org
    ```

You can now point your browser to https://insights.${BASE_DOMAIN} and start developing the server

