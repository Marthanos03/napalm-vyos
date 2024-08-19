Value HOURS (\S+)
Value MINUTES (\S+)
Value SECONDS (\S+)

Start
  ^Uptime:\s+${HOURS}h\s+${MINUTES}m\s+${SECONDS}s -> Record
  ^Uptime:\s+${MINUTES}m\s+${SECONDS}s -> Record
  ^Uptime:\s+${SECONDS}s -> Record
