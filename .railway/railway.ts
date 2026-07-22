import type { Project, Service } from "@railway/cli";

const project: Project = {
  name: "order",
  environments: [
    {
      name: "production",
      services: [
        {
          name: "api",
          source: {
            repo: "https://github.com/dcyzxz/order",
            branch: "master",
          },
          template: "python",
          buildCommand: "pip install -r requirements.txt",
          startCommand: "uvicorn main:app --host 0.0.0.0 --port $PORT",
          healthcheckPath: "/health",
          variables: {
            PORT: "8000",
            APP_NAME: "点菜小程序",
            APP_VERSION: "0.1.0",
            DEBUG: "false",
            API_PREFIX: "/api/v1",
            JWT_ALGORITHM: "HS256",
            JWT_EXPIRATION_HOURS: "72",
            LOG_LEVEL: "INFO",
            LOG_FORMAT: "json",
            ADMIN_USERNAME: "admin",
          },
        },
        {
          name: "db",
          template: "mysql",
        },
      ],
    },
  ],
};

export default project;
