# -*- coding: utf-8 -*-

import logging
import time
import matplotlib.pyplot as plt
import numpy as np
from library.hardware.Spectrometer.thorlabs_spectrometer import BFSpectrometer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
from blickfeld_measurement_instruments.daedalus.lsr import LSR_Adaptor
from blickfeld_measurement_instruments.instruments import NucleoI2C

def read_spectrum():
    plt.clf()
    n = 1
    bfspec = BFSpectrometer()
    bfspec.ccs.set_integration_time('1.ms')
    for i in range(n):
        bfspec.ccs.start_scan_trg()
        spectrum, wavelength_array, sat=bfspec.get_spectrum(not_saturated=False)
        plt.title('Spectral Data')
        plt.xlabel("Wavelength in nm")
        plt.ylabel("Intensity")
        print(f'{i}: saturated: {sat}')
        plt.plot(wavelength_array, spectrum, "-g", label = "Acquired")
        plt.show()
    return [spectrum, wavelength_array]

def spectral_analysis():
    intensity = read_spectrum()[0]
    wl = read_spectrum()[1]
    tolerance = len(intensity) * (0.02) # 2% of the data points
    start_index = int(np.argmax(intensity) - tolerance)
    stop_index = int(np.argmax(intensity) + tolerance + 1)
    spectrum_intensity = intensity[start_index: stop_index]
    spectrum_wl = wl[start_index: stop_index]
    plt.clf()
    plt.title('Spectral Data')
    plt.xlabel("Wavelength in nm")
    plt.ylabel("Intensity")
    plt.plot(spectrum_wl, spectrum_intensity)
    mx = np.random.randint(np.argmin(spectrum_wl), np.argmax(spectrum_wl),
    stop_index-start_index)
    cmx = np.sum(spectrum_wl * mx) / np.sum(mx)
    my= np.random.randint(0, np.argmax(abs(spectrum_intensity)),
    stop_index-start_index)
    cmy = np.sum(spectrum_intensity * my) / np.sum(my)
    print(f"Spectral CoM in x : {cmx:.3f}")
    print(f"Spectral CoM in y: {cmy:.3f}")
    plt.axvline(x=cmx, color="r", ls="--")
    plt.title(f"Spectral CoM: {cmx:.1f} Hz @ LSR Frequency of Hz")

plt.savefig("C:/Users/banda/Desktop/Dv_D/design_verification/test_measurements/CoM.png")
plt.show()

if __name__ == "__main__":
    with NucleoI2C(0x50) as i2c_master:
        lsr = LSR_Adaptor(i2c_master)
        status, fw = lsr.get_firmware_version()
    if not status == 0:
        logger.warning(f"Reading firmware version failed.")
    else:
        logger.info("Firmware version is: {}.{}.{}".format(*fw))
        status, lsr_status = lsr.get_status()
    if not status == 0:
        logger.warning(f"Reading lsr status failed.")
    else:
        logger.info(f"LSR status is {lsr_status}")
        status, temperature = lsr.get_temperature()
    if not status == 0:
        logger.warning(f"Reading temperature failed.")
    else:
        logger.info(f"Temperature is {temperature:2f} °C.")
        status, enabled = lsr.get_enable_reg()
    if not status == 0:
        logger.warning(f"Reading enabled flag failed.")
    else:
        logger.info(f"Laser output is {'enabled' if enabled else 'disabled'}")
    
    pulse = {
        "freq": 10,
        "charge_start": lsr.time_to_cycles(1e-6),
        "charge_stop": lsr.time_to_cycles(1.25e-6),
        "trig_delay": lsr.time_to_cycles(250e-9),
        "trig_pulsewidth": lsr.time_to_cycles(15e-9),
        "is_main": True,
    }
    
    # configure the adaptor board laser pulse settings
    lsr.configure_pulse(**pulse)
    # enable the LSR board (allows laser output, enables voltage)
    lsr.set_enable_reg(True)
    # set laser voltage to 12 V
    lsr.set_voltage(20.0) 
    time.sleep(1)
    
    status, voltage = lsr.get_voltage()
    if not status == 0:
        logger.warning(f"Reading laser voltage failed.")
    else:
        logger.info(f"Laser voltage is {voltage}")
    status, rep_rate = lsr.get_rep_rate()
    if not status == 0:
        logger.warning("Reading repetition rate failed.")
    else:
        logger.info(f"repetition rate (measured) is {rep_rate}")
        
    if rep_rate < 1000 and pulse["freq"] < 1000: # enable the adaptor board trigger signal
        print(lsr.get_temperature()[1])
    
    lsr.set_trigger_state(True)
    
    read_spectrum()
    spectral_analysis()
    
    print(lsr.get_status())
    
    lsr.set_trigger_state(False)
    lsr.set_enable_reg(False) 
