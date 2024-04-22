from machine import Pin, UART

class UartConsole():
    def __init__(self, uart_id: int, tx_pin: int, rx_pin: int, print_output=False, baudrate=115200):
        self.uart = UART(uart_id, baudrate=baudrate, tx=Pin(tx_pin), rx=Pin(rx_pin))
        self.uart.init(bits=8, parity=None, stop=1)
        self.print_output = print_output

    def write(self, buf):
        if self.print_output:
            print(buf)
        if not self.uart:
            return 0
        return self.uart.write(buf + '\n')
