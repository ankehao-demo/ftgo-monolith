FROM eclipse-temurin:8u432-b06-jre-alpine
RUN apk --no-cache add curl
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
WORKDIR /app
COPY build/libs/ftgo-application.jar .
RUN chown -R appuser:appgroup /app
USER appuser
HEALTHCHECK --start-period=30s --interval=5s CMD curl -f http://localhost:8080/actuator/health || exit 1
CMD java ${JAVA_OPTS} -jar ftgo-application.jar
