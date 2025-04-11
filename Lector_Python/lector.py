import serial
import time
import pymysql
import paramiko
from datetime import datetime
import pytz
from dotenv import load_dotenv
import os

load_dotenv()  # carga variables del archivo .env

PORT = os.getenv("PORT")
ZONE_ID = pytz.timezone(os.getenv("ZONE_ID"))

SSH_HOST = os.getenv("SSH_HOST")
SSH_USER = os.getenv("SSH_USER")
SSH_PASSWORD = os.getenv("SSH_PASSWORD")
LOCAL_PORT = int(os.getenv("LOCAL_PORT"))
REMOTE_PORT = int(os.getenv("REMOTE_PORT"))

MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")


def longitud_de_onda(i):
    return (
        9 +
        1e-11 * (i + 1) ** 4
        - 1e-7 * (i + 1) ** 3
        - 0.0026 * (i + 1) ** 2
        + 2.808 * (i + 1)
        + 302.4
    )


def ssh_tunnel():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(SSH_HOST, username=SSH_USER, password=SSH_PASSWORD)
    tunnel = client.get_transport().open_channel(
        "direct-tcpip", ("127.0.0.1", REMOTE_PORT), ("127.0.0.1", 0)
    )
    return client, tunnel


from sshtunnel import SSHTunnelForwarder

def insert_data(datetime_now, min_val, max_val):
    try:
        with SSHTunnelForwarder(
            (SSH_HOST, 22),
            ssh_username=SSH_USER,
            ssh_password=SSH_PASSWORD,
            remote_bind_address=('127.0.0.1', 3306),
            local_bind_address=('127.0.0.1', LOCAL_PORT)
        ) as tunnel:
            print("Túnel SSH abierto")

            conn = pymysql.connect(
                host="127.0.0.1",
                port=tunnel.local_bind_port,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                db=MYSQL_DB,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
            )

            with conn.cursor() as cursor:
                timestamp = datetime_now.astimezone(ZONE_ID).strftime('%Y-%m-%d %H:%M:%S')
                query = "INSERT INTO hd (`datetime`, `baja`, `alta`) VALUES (%s, %s, %s)"
                cursor.execute(query, (timestamp, min_val, max_val))
                conn.commit()
                print("Data inserted into DB.")
    except Exception as e:
        print(f"Error durante la inserción: {e}")


def main():
    try:
        ser = serial.Serial(PORT, baudrate=115200, timeout=1)
        print(f"Puerto serial {PORT} abierto.")
    except Exception as e:
        print(f"No se pudo abrir el puerto serial: {e}")
        return

    while True:
        valores = []
        buffer = ""
        ind = 0
        start_time = time.time()

        while ind < 20:
            if ser.in_waiting:
                read_data = ser.read(ser.in_waiting).decode("utf-8", errors="ignore")
                buffer += read_data
                if buffer.strip().endswith("a"):
                    valores.append(buffer.strip())
                    print(buffer.strip())
                    buffer = ""
                    print(f"-------------------------{ind}-------------------------\n")
                    ind += 1
                    start_time = time.time()
            elif time.time() - start_time > 360:
                print("Timeout: reiniciando puerto serial")
                ser.close()
                time.sleep(0.5)
                ser.open()
                start_time = time.time()

        # procesamiento
        datos = []
        for line in valores[1:]:  # ignoramos el primero como en Java
            parts = line.split(",")
            if len(parts) > 100:
                try:
                    num = float(parts[50].strip())
                    datos.append(num)
                except ValueError:
                    continue

        if datos:
            min_val = min(datos)
            max_val = max(datos)
            diferencia = max_val - min_val
            print(f"Diferencia: {diferencia:.2f}")

            if diferencia >= 120 or diferencia <= 15:
                insert_data(datetime.now(), min_val, max_val)

        print("Esperando 2 segundos...")
        time.sleep(2)


if __name__ == "__main__":
    main()
