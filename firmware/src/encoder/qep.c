
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
#include <src/timer/timer.h>
#include <src/encoder/qep.h>

#define QEP_TIMER                       PAC55XX_TIMERD
#define QEP_TIMERX                      TimerD

//=====================================
// QEP Input Port Definitions
//=====================================
#define QEPPHB_PORTNUM                  P6
#define QEPPHA_PORTNUM                  P5
#define QEPIDX_PORTNUM                  P4

QEPState state = {0};

void qep_init(void)
{
    pac5xxx_timer_clock_config(QEP_TIMERX, TXCTL_CS_ACLK, TXCTL_PS_DIV16);
    pac5xxx_timer_base_config(
        QEP_TIMERX, 
        0xFFFF, 
        AUTO_RELOAD, 
        TxCTL_MODE_UP, 
        TIMER_SLAVE_SYNC_DISABLE
    );

    // Enable QEP timer
    QEP_TIMER->QEPCTL.QEPEN = true;

    // Count on rising and falling edge
    QEP_TIMER->QEPCTL.CNTEDGE = RISING_FALLING_EDGE_BOTH;
    // Count on both A and B inputs
    QEP_TIMER->QEPCTL.CNTAB = PHASE_AB_BOTH;

    // Reset counter on Index
    QEP_TIMER->QEPCTL.IDXRST = NOT_RESET_TICKS;

    QEP_TIMER->QEPCTL.DIRIE = 0;                                               // 1--> enable direction change interrupt
    QEP_TIMER->QEPCTL.IFCLEAR = (1 << 0);
    
    QEP_TIMER->QEPCTL.PHAIE = 0;                                               // 1--> enable Phase A rising edge interrupt
    QEP_TIMER->QEPCTL.IFCLEAR = (1 << 1);
        
    QEP_TIMER->QEPCTL.PHBIE = 0;                                               // 1--> enable Phase B rising edge interrupt
    QEP_TIMER->QEPCTL.IFCLEAR = (1 << 2); 
        
    QEP_TIMER->QEPCTL.WRIE = 0;                                                // 1--> enable overflow or underflow in the TAQEPCTL.TICKS interrupt
    QEP_TIMER->QEPCTL.IFCLEAR = (1 << 3);
        
    QEP_TIMER->QEPCTL.IDXEVIE = 0;                                             // 1--> enable index event interrupt
    QEP_TIMER->QEPCTL.IFCLEAR = (1 << 4);

    // Select GPIO peripheral MUX
    PAC55XX_SCC->PDMUXSEL.QEPPHB_PORTNUM = 3;
    PAC55XX_SCC->PDMUXSEL.QEPPHA_PORTNUM = 3;
    PAC55XX_SCC->PDMUXSEL.QEPIDX_PORTNUM = 3;

    // Configure ports as inputs
    PAC55XX_GPIOD->MODE.QEPPHB_PORTNUM = IO_HIGH_IMPEDENCE_INPUT;
    PAC55XX_GPIOD->MODE.QEPPHA_PORTNUM = IO_HIGH_IMPEDENCE_INPUT;
    PAC55XX_GPIOD->MODE.QEPIDX_PORTNUM = IO_HIGH_IMPEDENCE_INPUT;

    // Disable pullups
    PAC55XX_SCC->PDPUEN.QEPPHB_PORTNUM = 0;
    PAC55XX_SCC->PDPUEN.QEPPHA_PORTNUM = 0;
    PAC55XX_SCC->PDPUEN.QEPIDX_PORTNUM = 0;

    // Disable pulldowns
    PAC55XX_SCC->PDPDEN.QEPPHB_PORTNUM = 0;
    PAC55XX_SCC->PDPDEN.QEPPHA_PORTNUM = 0;
    PAC55XX_SCC->PDPDEN.QEPIDX_PORTNUM = 0;
}

PAC5XXX_RAMFUNC uint16_t qep_get_pos_wrapped(void)
{
    // PAC55XX uses a uint16 to store the qep value. To get a value
    // that is wrapped in a single encoder turn, we need to first
    // unwrap into a continuous position, and then wrap to encoder
    // resolution.
    const int32_t raw_val = (uint16_t) QEP_TIMER->QEPCTL.TICKS;
    const int16_t diff = raw_val - state.prev_raw_val;
    state.prev_raw_val = raw_val;
    if (diff <= ENCODER_HALF_TICKS)
    {
        state.overflows += 1;
    }
    else if (diff > ENCODER_HALF_TICKS)
    {
        state.overflows -= 1;
    }
    raw_val += state.overflows * ENCODER_TICKS;
}
