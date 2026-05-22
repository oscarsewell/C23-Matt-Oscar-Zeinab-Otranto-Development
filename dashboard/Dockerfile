FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py data_access.py transformations.py ./

RUN mkdir -p ~/.streamlit

# Configure Streamlit to run without a browser
RUN echo "\
[server]\n\
headless = true\n\
port = 8501\n\
enableCORS = false\n\
" > ~/.streamlit/config.toml

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]
