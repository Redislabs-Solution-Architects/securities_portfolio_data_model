### Run within K8S cluster

Execute following commands in sequence, within the k8s cluster:

    export NAMESPACE=app-poc
    kubectl create namespace $NAMESPACE
    kubectl config set-context --current --namespace=$NAMESPACE

    kubectl apply -f app-config-map.yaml 
    kubectl apply -f app-jobs.yaml 
    kubectl apply -f app-deployment.yaml 
    kubectl apply -f app-service.yaml

