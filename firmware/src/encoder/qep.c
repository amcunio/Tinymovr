
//  * This file is part of the Tinymovr-Firmware distribution
//  * (https://github.com/yconst/tinymovr-firmware).
//  * Copyright (c) 2020 Ioannis Chatzikonstantinou.
//  * 
//  * This program is free software: you can redistribute it and/or modify  
//  * it under the terms of the GNU General Public License as published by  
//  * the Free Software Foundation, version 3.
//  *
//  * This program is distributed in the hope that it will be useful, but 
//  * WITHOUT ANY WARRANTY; without even the implied warranty of 
//  * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
//  * General Public License for more details.
//  *
//  * You should have received a copy of the GNU General Public License 
//  * along with this program. If not, see <http://www.gnu.org/licenses/>.

#include <src/common.h>
#include <src/encoder/qep.h>

#define QEP_TIMER                       PAC55XX_TIMERC
#define QEP_TIMERX                      TimerC

//=====================================
// QEP Input Port Definitions
//=====================================
#define PAC5XXX_GPIO_QEPPHA             PAC55XX_GPIOC
#define QEPPHB_PORTNUM                  P6

#define PAC5XXX_GPIO_QEPPHB             PAC55XX_GPIOC
#define QEPPHA_PORTNUM                  P5

#define PAC5XXX_GPIO_QEPIDX             PAC55XX_GPIOC
#define QEPIDX_PORTNUM                  P4

void qep_init(void)
{
    // Select GPIO peripheral MUX
    PAC55XX_SCC->PCMUXSEL.QEPPHB_PORTNUM = 3;
    PAC55XX_SCC->PCMUXSEL.QEPPHA_PORTNUM = 3;
    PAC55XX_SCC->PCMUXSEL.QEPIDX_PORTNUM = 3;

    // Configure ports as inputs
    PAC5XXX_GPIO_QEPPHB->MODE.QEPPHB_PORTNUM = 3;
    PAC5XXX_GPIO_QEPPHA->MODE.QEPPHA_PORTNUM = 3;
    PAC5XXX_GPIO_QEPIDX->MODE.QEPIDX_PORTNUM = 3;

    // Disable pullups
    PAC55XX_SCC->PCPUEN.QEPPHB_PORTNUM = 0;
    PAC55XX_SCC->PCPUEN.QEPPHA_PORTNUM = 0;
    PAC55XX_SCC->PCPUEN.QEPIDX_PORTNUM = 0;

    // Disable pulldowns
    PAC55XX_SCC->PCPDEN.QEPPHB_PORTNUM = 0;
    PAC55XX_SCC->PCPDEN.QEPPHA_PORTNUM = 0;
    PAC55XX_SCC->PCPDEN.QEPIDX_PORTNUM = 0;

    pac5xxx_timer_clock_config(QEP_TIMERX, TXCTL_CS_PCLK, TXCTL_PS_DIV1);

    // Count on rising and falling edge
    QEP_TIMER->QEPCTL.CNTEDGE = true;
    // Count on both A and B inputs
    QEP_TIMER->QEPCTL.CNTAB = true;

    // Reset counter on Index
    //QEP_TIMER->QEPCTL.IDXRST = false;

    // Configure QEP interrupts
    QEP_TIMER->QEPCTL.IDXEVIE = false;
    QEP_TIMER->QEPCTL.DIRIE = false;
    QEP_TIMER->QEPCTL.PHAIE = false;
    QEP_TIMER->QEPCTL.PHBIE = false;

    // Enabled QEP timer
    QEP_TIMER->QEPCTL.QEPEN = true;
}

PAC5XXX_RAMFUNC static inline uint16_t qep_get_counter_value(void)
{
    // Shift it from 31:16 bit to value from 15:0 bit, same 16 bits
    return  (uint16_t) ((QEP_TIMER->QEPCTL.TICKS) >> 16);
}
