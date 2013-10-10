# Imports
import webiopi

# Retrieve GPIO lib
GPIO = webiopi.GPIO

# -------------------------------------------------- #
# Initialization part                                #
# -------------------------------------------------- #

# Setup GPIOs
GPIO.setFunction(22, GPIO.OUT)
GPIO.setFunction(23, GPIO.OUT)
GPIO.setFunction(24, GPIO.OUT)
GPIO.setFunction(25, GPIO.OUT)
GPIO.setFunction(7, GPIO.OUT)
GPIO.setFunction(8, GPIO.OUT)
GPIO.setFunction(11, GPIO.OUT)
GPIO.setFunction(10, GPIO.OUT)
GPIO.setFunction(9, GPIO.OUT)
GPIO.setFunction(18, GPIO.OUT)

GPIO.output(7, GPIO.LOW)
GPIO.output(8, GPIO.LOW)
GPIO.output(9, GPIO.LOW)
GPIO.output(11, GPIO.LOW)
GPIO.output(18, GPIO.LOW)
GPIO.output(22, GPIO.LOW)
GPIO.output(23, GPIO.LOW)
GPIO.output(24, GPIO.LOW)
GPIO.output(25, GPIO.LOW)


# -------------------------------------------------- #
# Main server part                                   #
# -------------------------------------------------- #

# Instantiate the server on the port 8000, it starts immediately in its own thread
server = webiopi.Server(port=8000) #, login="incubator", password="letmein")
# or     webiopi.Server(port=8000, passwdfile="/etc/webiopi/passwd")

# -------------------------------------------------- #
# Loop execution part                                #
# -------------------------------------------------- #

# Run our loop until CTRL-C is pressed or SIGTERM received
webiopi.runLoop()

# -------------------------------------------------- #
# Termination part                                   #
# -------------------------------------------------- #

# Cleanly stop the server
server.stop()

# Reset GPIO functions
GPIO.setFunction(7, GPIO.IN)
GPIO.setFunction(8, GPIO.IN)
GPIO.setFunction(9, GPIO.IN)
GPIO.setFunction(11, GPIO.IN)
GPIO.setFunction(18, GPIO.IN)
GPIO.setFunction(22, GPIO.IN)
GPIO.setFunction(23, GPIO.IN)
GPIO.setFunction(24, GPIO.IN)
GPIO.setFunction(25, GPIO.IN)