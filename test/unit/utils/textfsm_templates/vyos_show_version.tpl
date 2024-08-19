Value VERSION (.+)
Value SERIAL_NUMBER (.+)
Value MODEL (.+)

Start
  ^Version:\s+${VERSION}
  ^Hardware model:\s+${MODEL}
  ^Hardware S\/N:\s+${SERIAL_NUMBER}
