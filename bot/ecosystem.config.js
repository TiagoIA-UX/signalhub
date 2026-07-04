module.exports = {
  apps: [
    {
      name: "signalhub",
      script: ".venv/Scripts/python.exe",
      args: "-m src.scheduler",
      cwd: __dirname,
      interpreter: "none",
      autorestart: true,
      restart_delay: 5000,
      max_restarts: 20,
      min_uptime: 10000,
      env: {
        NODE_ENV: "production",
      },
    },
  ],
};
