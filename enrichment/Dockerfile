FROM public.ecr.aws/lambda/python:3.14

COPY docker_requirements.txt ${LAMBDA_TASK_ROOT}/

RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/docker_requirements.txt

COPY enrichment_upload_lambda.py ${LAMBDA_TASK_ROOT}/
COPY enrichment_and_upload.py ${LAMBDA_TASK_ROOT}/

CMD ["enrichment_upload_lambda.lambda_handler"]
