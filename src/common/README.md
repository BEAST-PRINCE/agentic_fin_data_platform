# Common (`src/common/`)

## 🛠️ Why does this folder exist?

I created this folder to house all the shared utilities, configurations, and helper functions that multiple parts of my project need. By centralizing these, I avoid the dreaded "copy-paste" anti-pattern and ensure that things like logging, environment variable parsing, and database connections are handled consistently across the entire codebase.

## 📦 Responsibilities & Internal Structure

This directory acts as the glue for the project. Its responsibilities include:

* **Configuration Management:** Parsing `.env` files and providing typed settings objects to the rest of the application.
* **Logging Setup:** Configuring standard logging formats so that whether an error comes from a Spark job or an API endpoint, it looks the same and is easy to parse in Grafana.
* **Constants:** Centralizing magic strings, Kafka topic names, and file paths.
* **Shared Utilities:** Small helper functions for date formatting, string cleaning, or generic error handling.

## 🔄 Data Flow

There isn't a "flow" of data through this folder. Instead, it is imported by almost every other module in the `src/` directory. When the API starts up, or when a Spark job kicks off, they first look here to get their bearings (configurations) and their voice (loggers).

## 🔌 Extension Points

* If I ever decide to change my logging backend (e.g., sending logs to a centralized ELK stack instead of just stdout), I only have to change it here in the common logger setup, and the entire project will inherit the change instantly.
* New environment variables should be added to the configuration classes here to ensure they are validated on startup.

## 🐛 Debugging Tips

* **Missing Environment Variables:** If a service crashes immediately on startup complaining about a missing key, check the config parser here. It's designed to fail fast if the environment isn't set up correctly.
* **Silent Failures:** If you expect to see logs but don't, verify that the logging configuration in this folder hasn't accidentally set the global log level to `ERROR` or disabled console output.
