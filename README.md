# GitHub-CI-CD-ELT-Pipeline
CI/CD for Airflow ELT Pipeline on K8S using GitHub Action
# *Overview*
# *Prerequisites*
# *Project Flow*
The CI/CD jobs devide three section everyting done by ci_cd_airflow.yml:
1. lint -- Check formating with black
   ```yml
   lint:
    runs-on: self-hosted  # Use self-hosted runner for local access
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Verify Python version
        run: python3 --version
        
      - name: Install dependencies
        run: pip install -r requirements.txt --break-system-packages

      - name: Lint with flake8
        run: flake8 dags/ --count --show-source --statistics
   ```
2. test --  Validates DAG structure and ELT functions
   ```yml
   steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Verify Python version
        run: python3 --version
 
      - name: Install dependencies
        run: pip install -r requirements.txt --break-system-packages

      - name: Run tests
        run: pytest test/  # Validates DAG structure and ELT functions
   ```
3. deploy -- Deploying the DAG into minikube Airflow
   ```yaml
   name: Deploy DAG to Airflow in Minikube
        run: |
          # Verify namespace exists
          kubectl get namespace elt-pipeline || kubectl create namespace elt-pipeline
          # Get Airflow scheduler pod name with error handling
          # POD_NAME=$(kubectl get pods -n elt-pipeline -l app=airflow,component=scheduler -o jsonpath="{.items[0].metadata.name}" || echo "")
          POD_NAME=$(kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' | grep airflow-scheduler)
          if [ -z "$POD_NAME" ]; then
            echo "Error: No Airflow in namespace elt-pipeline"
            exit 1
          fi
          DAG_FOLDER=/opt/airflow/dags
          kubectl cp dags/elt_dag.py $POD_NAME:$DAG_FOLDER/elt_dag.py -n elt-pipeline
          kubectl exec -n elt-pipeline $POD_NAME -- airflow dags reserialize

   ```
