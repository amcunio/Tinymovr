
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
#include "src/system/system.h"
#include "src/ssp/ssp_func.h"
#include <src/encoder/encoder.h>

static struct EncoderState state = { 0 };

#define MAX_ALLOWED_DELTA_ADD (MAX_ALLOWED_DELTA + ENCODER_TICKS)
#define MAX_ALLOWED_DELTA_SUB (MAX_ALLOWED_DELTA - ENCODER_TICKS)
#define MIN_ALLOWED_DELTA_ADD (-MAX_ALLOWED_DELTA + ENCODER_TICKS)
#define MIN_ALLOWED_DELTA_SUB (-MAX_ALLOWED_DELTA - ENCODER_TICKS)

void encoder_init(void)
{
    ssp_init(SSPD, SSP_MS_MASTER, 0, 0); // Mode 0
    system_delay_us(16000); // ensure 16ms sensor startup time as per the datasheet
    encoder_queue_pos_command();
    encoder_update_pos(false);
}

PAC5XXX_RAMFUNC void encoder_queue_pos_command(void)
{
	ssp_write_one(SSPD, MA_CMD_ANGLE);
}

PAC5XXX_RAMFUNC int16_t encoder_get_pos(void)
{
    return state.position;
}

PAC5XXX_RAMFUNC void encoder_update_pos(bool check_error)
{
    while (!PAC55XX_SSPD->STAT.RNE) {}
    const int16_t position = (PAC55XX_SSPD->DAT.DATA) >> 3;

    if (check_error)
    {
    	const int16_t delta = state.position - position;
		if ( ((delta > MAX_ALLOWED_DELTA) || (delta < -MAX_ALLOWED_DELTA)) &&
		     ((delta > MAX_ALLOWED_DELTA_ADD) || (delta < MIN_ALLOWED_DELTA_ADD)) &&
		     ((delta > MAX_ALLOWED_DELTA_SUB) || (delta < MIN_ALLOWED_DELTA_SUB)) )
		{
			add_error_flag(ERROR_ENCODER_READING_UNSTABLE);
		}
    }
    state.position = position;
}
