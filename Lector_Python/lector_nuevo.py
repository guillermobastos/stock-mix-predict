import serial
import time
from datetime import datetime
import pytz
import mysql.connector
from sshtunnel import SSHTunnelForwarder
from typing import Optional
import os
from dotenv import load_dotenv
import vonage
from typing import Optional

# Cargar variables de entorno
load_dotenv()

class Config:
    # Serial
    SERIAL_PORT = os.getenv('SERIAL_PORT')
    BAUD_RATE = int(os.getenv('BAUD_RATE', '115200'))
    
    # Vonage
    VONAGE_API_KEY = os.getenv('VONAGE_API_KEY')
    VONAGE_API_SECRET = os.getenv('VONAGE_API_SECRET')
    VONAGE_FROM_NUMBER = os.getenv('VONAGE_FROM_NUMBER')
    VONAGE_TO_NUMBER = os.getenv('VONAGE_TO_NUMBER')
    
    # SSH
    SSH_USER = os.getenv('SSH_USER')
    SSH_PASSWORD = os.getenv('SSH_PASSWORD')
    SSH_HOST = os.getenv('SSH_HOST')
    SSH_PORT = int(os.getenv('SSH_PORT', '22'))
    
    # MySQL
    MYSQL_USER = os.getenv('MYSQL_USER')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')
    MYSQL_HOST = os.getenv('MYSQL_HOST')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3306'))
    
    # Timezone
    TIMEZONE = os.getenv('TIMEZONE')

class Lector:
    text = []
    array_longitudes = []
    array_list = []
    blanco = []
    muestras = {}
    valores_doub = []
    PORT = "/dev/serial/by-id/usb-Arduino__www.arduino.cc__0042_851333130313511062C0-if00"
    ZONE_ID = pytz.timezone('Europe/Madrid')

    @staticmethod
    def longitud_de_onda(num: int) -> float:
        num_d = float(num)
        salida = (9 + 
                 (10 ** -11) * ((num_d + 1) ** 4) - 
                 (10 ** -7) * ((num + 1) ** 3) - 
                 0.0026 * ((num_d + 1) ** 2) + 
                 2.808 * (num_d + 1) + 
                 302.4)
        return salida

    @staticmethod
    def check_numerico(numero: str) -> float:
        try:
            if numero:
                mod = numero.replace('\0', '')
                return float(mod.strip())
        except ValueError:
            print(f"Error NumberFormatException value: {numero}")
        return 0.0

    @staticmethod
    def send_message(mensaje: str) -> None:
        """
        Envía un mensaje SMS usando la API de Vonage.

        Args:
            mensaje: El texto del mensaje a enviar.
        """
        # Configuración del cliente Vonage con tus credenciales
        client = vonage.Client(
            key=Config.VONAGE_API_KEY,
            secret=Config.VONAGE_API_SECRET
        )

        sms = vonage.Sms(client)

        try:
            # Enviar el mensaje SMS
            response_data = sms.send_message({
                'from': Config.VONAGE_FROM_NUMBER,
                'to': Config.VONAGE_TO_NUMBER,  # Número de teléfono en formato internacional
                'text': mensaje
            })

            # Verificar el estado de la respuesta
            if response_data["messages"][0]["status"] == "0":
                print("Mensaje enviado exitosamente.")
            else:
                error_message = response_data["messages"][0].get("error-text", "Error desconocido")
                print(f"Fallo en el envío del mensaje: {error_message}")

        except Exception as e:
            print(f"Error al enviar el mensaje: {str(e)}")

    @staticmethod
    def init_ssh_session() -> Optional[SSHTunnelForwarder]:
        try:
            server = SSHTunnelForwarder(
                (Config.SSH_HOST, Config.SSH_PORT),
                ssh_username=Config.SSH_USER,
                ssh_password=Config.SSH_PASSWORD,
                remote_bind_address=(Config.REMOTE_MYSQL_HOST, Config.REMOTE_MYSQL_PORT),
                local_bind_address=('127.0.0.1', 3309)
            )
            server.start()
            print("SSH tunnel established successfully")
            return server
        except Exception as e:
            print(f"Error establishing SSH tunnel: {e}")
            return None

    @staticmethod
    def init_mysql_connection() -> Optional[mysql.connector.connection.MySQLConnection]:
        while True:
            try:
                connection = mysql.connector.connect(
                    host='127.0.0.1',
                    port=3309,
                    user=Config.MYSQL_USER,
                    password=Config.MYSQL_PASSWORD,
                    database=Config.REMOTE_MYSQL_DB
                )
                print("MySQL connection established successfully")
                return connection
            except mysql.connector.Error as err:
                print(f"Error connecting to MySQL: {err}")
                time.sleep(5)

    @staticmethod
    def send_data_to_table(datetime_obj: datetime, baja: float, alta: float) -> None:
        server = None
        connection = None
        
        while True:
            try:
                print("Initializing SSH session...")
                server = Lector.init_ssh_session()
                
                if server is None:
                    print("Failed to establish SSH connection. Retrying in 5 seconds...")
                    time.sleep(5)
                    continue
                
                print("Initializing MySQL connection...")
                connection = Lector.init_mysql_connection()
                
                if connection is None:
                    print("Failed to establish MySQL connection. Retrying in 5 seconds...")
                    if server:
                        server.stop()
                    time.sleep(5)
                    continue
                
                break
            except Exception as e:
                print(f"Connection error: {e}")
                time.sleep(5)

        try:
            # Convert to Spain timezone
            localized_dt = datetime_obj.astimezone(Lector.ZONE_ID)
            
            tabla = "hd"
            sql_query = f"INSERT INTO {tabla} (`datetime`, `baja`, `alta`) VALUES (%s, %s, %s);"
            print(f"SQL Query: {sql_query}")
            
            cursor = connection.cursor()
            cursor.execute(sql_query, (localized_dt, baja, alta))
            connection.commit()
            
            print(f"Rows inserted: {cursor.rowcount}")
            cursor.close()
        except Exception as e:
            print(f"Error inserting data: {e}")
        finally:
            if connection and connection.is_connected():
                connection.close()
                print("MySQL connection closed")
            if server:
                server.stop()
                print("SSH tunnel closed")

    @staticmethod
    def main() -> None:
        # Initialize wavelength array
        Lector.array_longitudes = [Lector.longitud_de_onda(i) for i in range(288)]
        
        # Serial port configuration
        baud_rate = 115200
        timeout = 20  # seconds
        
        try:
            mi_serial_port = serial.Serial(Lector.PORT, baud_rate, timeout=timeout)
            print(f"\n{mi_serial_port.port} is open.")
        except serial.SerialException as e:
            print(f"Could not open port: {e}")
            return

        while True:
            ind = 0
            valores = []
            buffer = ""
            last_data_received_time = time.time()
            timeout_threshold = 3  # 3 seconds
            
            try:
                while ind < 21:
                    if mi_serial_port.in_waiting > 0:
                        read_buffer = mi_serial_port.read(mi_serial_port.in_waiting)
                        s = read_buffer.decode('utf-8')
                        buffer += s
                        
                        if buffer.strip().endswith('a'):
                            valores.append(buffer.strip())
                            print(buffer)
                            buffer = ""
                            ind += 1
                            last_data_received_time = time.time()
                    else:
                        if time.time() - last_data_received_time > timeout_threshold:
                            print(f"Timeout: No data received in {timeout_threshold} seconds.")
                            
                            try:
                                print("Restarting serial port...")
                                mi_serial_port.close()
                                time.sleep(0.5)
                                mi_serial_port.open()
                                mi_serial_port.reset_input_buffer()
                                last_data_received_time = time.time()
                            except Exception as e:
                                print(f"Error during serial port restart: {e}")
            except Exception as e:
                print(f"Error reading from port: {e}")
            
            if valores:
                valores.pop(0)
            print(valores)
            
            # Process data
            valores_doub = []
            for val in valores:
                linea = val.strip().split(',')
                print(f"Quantity per line -> {len(linea)}")
                if len(linea) > 100:
                    max_val = Lector.check_numerico(linea[50].strip())
                    valores_doub.append(max_val)
            
            for val in valores_doub:
                print(val)
            
            if valores_doub:
                min_num = min(valores_doub)
                max_num = max(valores_doub)
                
                # Check thresholds
                diferencia = 120
                umbral_minimo = 15
                print(f"The difference is: {max_num - min_num:.2f}")
                
                if (max_num - min_num) >= diferencia:
                    Lector.send_data_to_table(datetime.now(), min_num, max_num)
                    # Lector.send_message("Alarm: Difference exceeded threshold.")
                if (max_num - min_num) <= umbral_minimo:
                    Lector.send_data_to_table(datetime.now(), min_num, max_num)
                    # Lector.send_message("Sensor error: Difference below minimum threshold.")
            
            try:
                print("Waiting 6 seconds before repeating...")
                time.sleep(6)
            except KeyboardInterrupt:
                print("Program interrupted by user")
                mi_serial_port.close()
                break

if __name__ == "__main__":
    Lector.main()