.syntax unified
.arm
.text

    push {r4,r5,r6,lr}
    sub sp,sp,#8
    ldr r4,[sp,#24]
    ldr r5,[sp,#28]
    str r4,[sp]
    str r5,[sp,#4]
    bl .
    mov r6,r0
    adr r0,setting_id
    adr r1,setting_caption
    adr r2,button_caption
    mov r3,#0
    adr r4,open_dialog
    str r4,[sp]
    mov r5,#0
    str r5,[sp,#4]
    bl .
    mov r0,r6
    add sp,sp,#8
    pop {r4,r5,r6,pc}
open_dialog:
    push {r4,lr}
    sub sp,sp,#8
    adr r0,action
    mov r1,#0
    mov r2,#0
    mov r3,#0
    mov r4,#0
    str r4,[sp]
    str r4,[sp,#4]
    bl .
    add sp,sp,#8
    pop {r4,pc}
setting_id:
    .asciz "button_dts_pcm_settings"
setting_caption:
    .asciz "dts_pcm_setting_label"
button_caption:
    .asciz "dts_pcm_setting_button"
action:
    .asciz "com.dunehd.pcm.DTS_SETTINGS"
