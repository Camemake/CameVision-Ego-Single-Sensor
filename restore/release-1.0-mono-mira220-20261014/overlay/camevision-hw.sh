#!/bin/sh
# MonoCamStack_Soc V5 + Power V3 — rail and wake GPIOs.
# Camera LDOs live on the power board. Wi-Fi CHIP_EN is Q1 via WIFI_RST (DT pwrseq).
# Do not steal CAM_PWDN (GPIO4_A6) or WIFI_RST (GPIO3_B2); those belong to the kernel.

LOG=/userdata/hw-rails.log
: > "$LOG"
log() { echo "$(date +%T) $*" | tee -a "$LOG"; }

export_out() {
	n=$1
	val=$2
	name=$3
	if [ ! -d /sys/class/gpio/gpio$n ]; then
		if ! echo $n > /sys/class/gpio/export 2>/dev/null; then
			log "skip $name gpio$n (busy)"
			return 1
		fi
	fi
	echo out > /sys/class/gpio/gpio$n/direction
	echo $val > /sys/class/gpio/gpio$n/value
	log "$name gpio$n=$val"
}

if [ -f /userdata/camevision-am.on ]; then
	# Mono AM: 2.5 V, 1.35 V, 1.8 V, then CAM0_RST high.
	export_out 8 1 PWR_EN_2.5V
	export_out 10 1 PWR_EN_1.35V
	sleep 0.02
	export_out 9 1 PWR_EN_1.8V
	sleep 0.05
	export_out 199 1 CAM0_RST
else
	# GPIO0_B0 PWR_EN_2.8V (U3 +2.8V_AVDD), GPIO0_B1 PWR_EN_1.5V (U4 +1.5V_DVDD)
	export_out 8 1 PWR_EN_2.8V
	export_out 9 1 PWR_EN_1.5V
fi
# GPIO2_A4 WIFI_SOC_PWCTL / HOST_WAKE_WL
export_out 68 1 WIFI_SOC_PWCTL
sleep 0.05
log "HW_RAILS_READY"
exit 0
