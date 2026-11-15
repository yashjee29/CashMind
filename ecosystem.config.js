module.exports = {
  apps: [
    {
      name: "cashmind",
      script: ".venv/bin/uvicorn",
      args: "app.main:app --host 0.0.0.0 --port 9102",
      interpreter: "none",
      restart_delay: 3000,
      max_restarts: 10,
    },
  ],
};
