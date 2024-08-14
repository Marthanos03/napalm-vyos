from napalm_vyos import VyosDriver

driver = VyosDriver(hostname='192.168.0.20', username='vyos', password='vyos')

print(driver.is_alive())

driver.open()

print(driver.is_alive())

print(driver.get_facts())
print(driver.get_interfaces())
print(driver.get_interfaces_counters())
print(driver.get_interfaces_ip())
print(driver.get_config())

driver.close()

print(driver.is_alive())
