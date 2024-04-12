## Problem
As a part 

## Requirements
- gcloud cli
- terraform

## Steps

- Download the Helsinki City bikes data set from [kaggle](https://www.kaggle.com/datasets/geometrein/helsinki-city-bikes?resource=download)

- in Google-Cloud-Services console, create a new project.


- init your shell, gcloud tool and terraform
```shell
# Set the project name in shell
export GCS_PROJECT=<your-gcp-project-id>;

#login to gcs using gcloud tool
gcloud auth login;

#Set the current project to the one created
gcloud config set project $GCS_PROJECT;

#set the project for terraform in the current shell
export TF_VAR_project=$GCS_PROJECT;
```

- init terraform state file
```shell
terraform init
```

- Check changes to new infra plan. Notice that terraform commands must run in the same shell you used to login to GCS, in order to have credentials to access the cloud.
```shell
terraform plan"
```

- Create new infra
```shell
terraform apply"
```

- upload the dataset to bucket
```shell
gcloud storage cp <data-set-zip-file-path> gs://zoomcamp_project_pfcllotsb7jsqqvbjrnw3s/zoomcamp-dataset
```

- When done, take down the infrastructure.
```shell
terraform destroy
```


