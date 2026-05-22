FROM public.ecr.aws/lambda/python:3.14

COPY docker_requirements.txt ${LAMBDA_TASK_ROOT}/

RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/docker_requirements.txt

COPY social_posting_lambda.py ${LAMBDA_TASK_ROOT}/
COPY bluesky_functions.py ${LAMBDA_TASK_ROOT}/

CMD ["social_posting_lambda.lambda_handler"]
