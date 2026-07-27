# Ingestion (`src/ingestion/`)

## 📥 Why does this folder exist?

Data is useless if it's stuck on a website. I built this folder to serve as the gateway between the outside world and my Lakehouse. It handles the critical task of taking raw data from my scrapers, packaging it up, and reliably pushing it into my messaging system (Kafka) so that the rest of the architecture can process it asynchronously.

## 🏭 Responsibilities & Internal Structure

The primary residents of this folder are my Kafka Producers.

Their responsibilities include:
* **Message Serialization:** Taking Python dictionaries from the scrapers and converting them into JSON payloads suitable for Kafka.
* **Reliable Delivery:** Handling network hiccups, retries, and ensuring that messages actually make it to the Kafka broker.
* **Topic Routing:** Ensuring that financial news goes to the news topic, and market data goes to the market data topic.

## 🔄 Data Flow

The flow here is short but critical:

`Scraper Output (Python Dicts)` ➔ `Ingestion Producer` ➔ `JSON Serialization` ➔ `Kafka Topic`

Once the data hits the Kafka topic, this folder's job is done. It hands off the baton to the Bronze layer spark consumers living in `src/processing/`.

## 🔌 Dependencies & Extension Points

* **Dependencies:** This code relies heavily on the `confluent-kafka` or `kafka-python` library and expects a running Kafka broker (usually managed by Docker Compose in `infra/`).
* **Extension Points:** If I ever need to add a new data source (e.g., a real-time WebSocket feed for stock prices), I will build a new producer script here to ingest that specific stream and route it to a new topic.

## 🐛 Debugging Tips

* **Kafka Won't Connect:** The most common issue here is Docker networking. Ensure the `KAFKA_BOOTSTRAP_SERVERS` environment variable points to the correct local address and port.
* **Silent Dropping:** If scrapers are running but no data is appearing in the Bronze layer, check if the producer in this folder is silently dropping messages due to serialization errors (e.g., trying to JSON serialize a `datetime` object without converting it to a string first).
