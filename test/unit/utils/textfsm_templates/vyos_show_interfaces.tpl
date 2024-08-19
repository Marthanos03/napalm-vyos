Value INTERFACE (\S+)
Value IP_ADDRESS (\S+)
Value MAC_ADDRESS (\S+)
Value VRF (\S+)
Value MTU (\d+)
Value STATE_LINK (\S+)

Start
  ^${INTERFACE}\s+${IP_ADDRESS}\s+${MAC_ADDRESS}\s+${VRF}\s+${MTU}\s+${STATE_LINK} -> Record
