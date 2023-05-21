# README

## Deploy to VDS\[Ubuntu 22.04]

#### `root` user

```
adduser airbot;
```

```
usermod -aG sudo airbot;
sudo apt update && sudo apt upgrade;
apt install python3;
apt install python3-venv;
apt install python3-pip;
apt install postgresql postgresql-contrib;
apt install redis;
reboot;
```

#### `airbot` user

```
sudo mkdir -m 777 -p /var/airbot/air_delivery
```

* **upload source code via SFTP to `/var/airbot/air_delivery/`**

```
cd /var/airbot/air_delivery;
pip install -r requirements.txt;
python3 -m venv venv;
sudo nano /etc/systemd/system/airbot.service;
```

* **airbot.service**
  * type `YOUR_PASSWORD`
  *   type `YOUR_BOT_TOKEN`

      ```
      [Unit]
      Description=airbot_service
      After=syslog.target
      After=network.target

      [Service]
      Type=simple
      User=airbot
      WorkingDirectory=/var/airbot/air_delivery
      Environment="PYTHONUNBUFFERED=1"
      Environment="BOT_TOKEN=YOUR_BOT_TOKEN"
      Environment="PGADMIN=postgres"
      Environment="PGADMINPASS=YOUR_PASSWORD"
      ExecStart=/usr/bin/python /var/airbot/air_delivery/app.py
      Restart=on-failure
      RestartSec=5s

      [Install]
      WantedBy=multi-user.target
      ```
*   **postgres database**

    ```
    cp -a /var/airbot/air_delivery/data/supporter_sources/country/country.csv /tmp;
    cp -a /var/airbot/air_delivery/data/supporter_sources/airport/airport.csv /tmp/;
    cp -a /var/airbot/air_delivery/data/database/airbot.sql /tmp; 
    ```

    ```
    systemctl start postgresql.service;
    sudo -i -u postgres;
    ```

    ```
    createdb airbot; 
    psql -d airbot;
    ```

    *   type `YOUR_PASSWORD`

        ```
        CREATE schema bot;
        SET schema 'bot';
        ALTER USER postgres PASSWORD 'YOUR_PASSWORD';
        ```

    ```
    \i /tmp/airbot.sql;
    ```

    ```
    COPY bot.country FROM '/tmp/country.csv' DELIMITER ',' CSV HEADER;
    COPY bot.airport FROM '/tmp/airport.csv' DELIMITER ',' CSV HEADER;
    ```

    ```
    \q
    ```

    ```
    exit;
    ```

    *   delete postgres

        ```
        sudo apt-get --purge remove postgresql
        sudo apt-get purge postgresql*
        sudo apt-get --purge remove postgresql postgresql-doc postgresql-common
        ```
*   **systemctl commands**

    ```
    sudo systemctl daemon-reload;
    sudo systemctl enable airbot.service;
    sudo systemctl start airbot.service;
    sudo systemctl status airbot.service;
    ```

