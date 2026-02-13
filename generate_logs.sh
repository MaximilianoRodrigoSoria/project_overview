#!/bin/bash

# Script para generar logs simulados de errores Java
# Crea archivo con errores comunes: NullPointerException, SQLException, HTTP Timeout

set -e

OUTPUT_FILE="datasets/generated_logs.txt"

echo "=== Generador de Logs Simulados ==="

# Crear directorio datasets si no existe
mkdir -p datasets

# Generar logs simulados
echo "[INFO] Generando logs en $OUTPUT_FILE..."

cat > "$OUTPUT_FILE" << 'EOF'
2026-02-13 08:30:15 ERROR [main] com.example.service.UserService - Error al procesar solicitud
java.lang.NullPointerException: Cannot invoke method on null object
	at com.example.service.UserService.getUserById(UserService.java:45)
	at com.example.controller.UserController.getUser(UserController.java:89)
	at com.example.filter.AuthFilter.doFilter(AuthFilter.java:34)
	at org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:193)
	at org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:166)

2026-02-13 08:31:42 WARN [pool-2-thread-3] com.example.dao.DatabaseConnection - Reintentando conexión a la base de datos

2026-02-13 08:31:55 ERROR [pool-2-thread-3] com.example.dao.UserRepository - Error en consulta SQL
java.sql.SQLException: Connection timeout after 30000ms
	at com.mysql.jdbc.ConnectionImpl.execSQL(ConnectionImpl.java:2712)
	at com.mysql.jdbc.PreparedStatement.executeInternal(PreparedStatement.java:2155)
	at com.mysql.jdbc.PreparedStatement.executeQuery(PreparedStatement.java:2322)
	at com.example.dao.UserRepository.findUserByEmail(UserRepository.java:67)
	at com.example.service.AuthService.authenticate(AuthService.java:123)

2026-02-13 08:32:10 INFO [main] com.example.Application - Iniciando aplicación v2.3.1

2026-02-13 08:33:28 ERROR [http-nio-8080-exec-5] com.example.client.PaymentClient - Timeout en petición HTTP
java.net.SocketTimeoutException: Read timed out
	at java.net.SocketInputStream.socketRead0(Native Method)
	at java.net.SocketInputStream.socketRead(SocketInputStream.java:116)
	at java.net.SocketInputStream.read(SocketInputStream.java:171)
	at com.example.client.PaymentClient.processPayment(PaymentClient.java:156)
	at com.example.service.OrderService.createOrder(OrderService.java:234)
	at com.example.controller.OrderController.placeOrder(OrderController.java:78)

2026-02-13 08:34:05 WARN [scheduler-1] com.example.jobs.CleanupJob - No se encontraron registros antiguos para limpiar

2026-02-13 08:35:17 ERROR [main] com.example.config.AppConfig - Fallo al cargar configuración
java.lang.NullPointerException: Configuration property 'database.url' is null
	at com.example.config.AppConfig.loadDatabaseConfig(AppConfig.java:89)
	at com.example.config.AppConfig.initialize(AppConfig.java:45)
	at com.example.Application.main(Application.java:23)

2026-02-13 08:36:42 INFO [main] com.example.service.CacheService - Cache inicializado correctamente

2026-02-13 08:37:55 ERROR [async-worker-7] com.example.service.EmailService - Error enviando email
javax.mail.MessagingException: Could not connect to SMTP host
	at com.sun.mail.smtp.SMTPTransport.openServer(SMTPTransport.java:2189)
	at com.sun.mail.smtp.SMTPTransport.protocolConnect(SMTPTransport.java:740)
	at com.example.service.EmailService.sendEmail(EmailService.java:112)

2026-02-13 08:38:20 ERROR [main] com.example.dao.ProductRepository - SQLException durante actualización
java.sql.SQLException: Duplicate entry '12345' for key 'PRIMARY'
	at com.mysql.jdbc.SQLError.createSQLException(SQLError.java:1073)
	at com.mysql.jdbc.MysqlIO.checkErrorPacket(MysqlIO.java:4074)
	at com.example.dao.ProductRepository.updateStock(ProductRepository.java:201)
	at com.example.service.InventoryService.adjustInventory(InventoryService.java:89)

2026-02-13 08:39:45 WARN [main] com.example.util.RetryUtil - Reintento 3/3 fallido, abortando operación
EOF

# Verificar creación exitosa
if [ -f "$OUTPUT_FILE" ]; then
    LINE_COUNT=$(wc -l < "$OUTPUT_FILE")
    echo "[OK] Archivo generado exitosamente"
    echo "[INFO] Total de líneas: $LINE_COUNT"
    echo "[INFO] Ubicación: $OUTPUT_FILE"
else
    echo "[ERROR] No se pudo crear el archivo"
    exit 1
fi

echo "=== Generación completada ==="
