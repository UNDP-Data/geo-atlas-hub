This folder holds the config files and specs to create a production ready KinD cluster that includes:

- Kubernetes Gateway API routing and load balancing
- IP provisioning
- automated certificate management through cert manager
    - one shared wildcard cert for *.undpgeohub.org domain
- oauth2-proxy authentication based on Github
- demo apps
    - simple demo app 
    - oauth2 based demoapp

The result is a KIND cluster ready for hosting apps as close as possible to a
real production grade Kubernetes cluster.

The reason is simple, namely to create a dev environment that is as close as 
possible to a production environment as to minimize development friction considering that
Insights Hub is a complex service integrating complex components like [Git](https://git-scm.com/), [Marimo](https://marimo.io/), 
[NiceGUI](https://nicegui.io/) and [FastAPI](https://fastapi.tiangolo.com/) all behind an [oauth2](https://oauth.net/2/) wall.


### Setup

The KinD based infrastructure needs to be set up in following order:

1. cluster
2. ingress
3. cert
4. oauth


### Required tools and assumptions

---

However, before moving on to the setup several assumptions are made:

- [x] docker is installed and available


Follow [docker installation instructions](https://docs.docker.com/engine/install/)

 - [x] KinD is installed and available

```shell
[ $(uname -m) = x86_64 ] && curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
[ $(uname -m) = aarch64 ] && curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-arm64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

```
```shell
kind version
```

- [x] kubectl is installed and available and configured to work with KIND


Follow [kubectl installation guide](https://kubernetes.io/docs/tasks/tools/)


> [!IMPORTANT]
> The kubectl needs to be configured to use KIND cluster and this can be done manually. However,KIND automatically 
> updates your default ~/.kube/config file when you run *kind create cluster*

- [x] helm is installed and available
Follow [helm installation guide](https://helm.sh/docs/intro/install/)

- [x] envsubst is installed and available

```shell
#Ubuntu / Debian: 

sudo apt-get install gettext-base

#Fedora / RHEL / CentOS: 

sudo dnf install gettext

#Alpine Linux: 

apk add gettext

#Arch Linux: 

sudo pacman -S gettext
```


  
- create test cluster to update kube cfg
```shell
 kind create cluster --name testcluster
```
- dump cluster info 
```shell
kubectl cluster-info dump -o yaml
```
- delete testcluster
```shell
 kind delete cluster --name testcluster
```

### Setup

---

To generate the whole infrastructure **ensure .env files** in every component/subfolder are 
filled in correctly with the required information/values. There are two possible approaches: manual
where each component is installed independently, considering its required dependencies or running the global
[setup script](./setup.sh)


```shell
./setup.sh
```
There is an expected delay meaning that some time (<3 min usually) needs to pass until the gateway transitions to programmed
This is mainly because the certificate provisioning

Check the setup
```shell
kubectl get httproute -A

kubectl get gateway -A
```
Query the Gateway IP directly with TLS Server Name Indication (SNI) to confirm the Let's Encrypt certificate is serving correctly:

```shell
BASE_DOMAIN=""
curl -kvI --resolve "auth.{$BASE_DOMAIN}:443:172.20.0.5" https://auth.{$BASE_DOMAIN}/oauth2/sign_in 2>&1 | grep -E "(CN=|subjectAltName|HTTP/)"
*  subject: CN=undpgeohub.org
*  issuer: C=US; O=Let's Encrypt; CN=(STAGING) Dastardly Durum YR1
* using HTTP/1.x
> HEAD /oauth2/sign_in HTTP/1.1
< HTTP/1.1 200 OK
HTTP/1.1 200 OK


```


To access the demo-app in browser you need to add the ip of the load balancer and the auth svc
to the /etc/hosts


```
GATEWAY_IP=$(kubectl get gateway cluster-gateway -n default -o jsonpath='{.status.addresses[*].value}' | tr ' ' '\n' | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' | head -n 1)
echo "Gateway IP: ${GATEWAY_IP}"
echo "${GATEWAY_IP} auth.${BASE_DOMAIN} " | sudo tee -a /etc/hosts
```

you can point now the browser to

http:/auth.{$BASEDOMAIN}

### Teardown

When it comes to removing all the KIND infrastructure it is best to proceed in following order:

1. oauth
2. cert
3. ingres (cloud provider and ip)
4. cluster


This can be done manually from each component's subfolder or using the global
[teardown.sh](./teardown.sh)

```shell
./teardown.sh
```
To check the infrastructure was wiped out:
```shell
kind get clusters
docker ps -a --filter "name=kind"
```