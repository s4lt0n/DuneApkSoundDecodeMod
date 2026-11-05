.class public final Lcom/dunehd/shell/settings/DtsPcmSettings$ShowDialog;
.super Ljava/lang/Object;
.implements Ljava/lang/Runnable;
.field private final activity:Landroid/app/Activity;

.method public constructor <init>(Landroid/app/Activity;)V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Lcom/dunehd/shell/settings/DtsPcmSettings$ShowDialog;->activity:Landroid/app/Activity;
    return-void
.end method

.method public run()V
    .locals 6
    iget-object v1, p0, Lcom/dunehd/shell/settings/DtsPcmSettings$ShowDialog;->activity:Landroid/app/Activity;
    invoke-virtual {v1}, Landroid/app/Activity;->isFinishing()Z
    move-result v0
    if-nez v0, :done
    :try_start
    new-instance v0, Landroid/app/AlertDialog$Builder;
    invoke-direct {v0, v1}, Landroid/app/AlertDialog$Builder;-><init>(Landroid/content/Context;)V
    const-string v2, "dts_pcm_dialog_title"
    invoke-static {v1, v2}, Lcom/dunehd/shell/settings/DtsPcmSettings;->text(Landroid/content/Context;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v2
    invoke-virtual {v0, v2}, Landroid/app/AlertDialog$Builder;->setTitle(Ljava/lang/CharSequence;)Landroid/app/AlertDialog$Builder;
    const/4 v2, 0x1
    new-array v3, v2, [Ljava/lang/CharSequence;
    const-string v4, "dts_pcm_checkbox"
    invoke-static {v1, v4}, Lcom/dunehd/shell/settings/DtsPcmSettings;->text(Landroid/content/Context;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v4
    const/4 v5, 0x0
    aput-object v4, v3, v5
    new-array v4, v2, [Z
    invoke-static {}, Lcom/dunehd/shell/settings/DtsPcmSettings;->isEnabled()Z
    move-result v2
    aput-boolean v2, v4, v5
    new-instance v2, Lcom/dunehd/shell/settings/DtsPcmSettings$Choice;
    invoke-direct {v2, v1}, Lcom/dunehd/shell/settings/DtsPcmSettings$Choice;-><init>(Landroid/content/Context;)V
    invoke-virtual {v0, v3, v4, v2}, Landroid/app/AlertDialog$Builder;->setMultiChoiceItems([Ljava/lang/CharSequence;[ZLandroid/content/DialogInterface$OnMultiChoiceClickListener;)Landroid/app/AlertDialog$Builder;
    const-string v2, "dts_pcm_done"
    invoke-static {v1, v2}, Lcom/dunehd/shell/settings/DtsPcmSettings;->text(Landroid/content/Context;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v2
    const/4 v3, 0x0
    invoke-virtual {v0, v2, v3}, Landroid/app/AlertDialog$Builder;->setPositiveButton(Ljava/lang/CharSequence;Landroid/content/DialogInterface$OnClickListener;)Landroid/app/AlertDialog$Builder;
    invoke-virtual {v0}, Landroid/app/AlertDialog$Builder;->show()Landroid/app/AlertDialog;
    :try_end
    goto :done
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :failure
    :failure
    move-exception v0
    const-string v2, "DtsPcmSettings"
    invoke-static {v2, v2, v0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I
    const-string v2, "dts_pcm_ui_error"
    invoke-static {v1, v2}, Lcom/dunehd/shell/settings/DtsPcmSettings;->text(Landroid/content/Context;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v2
    const/4 v3, 0x1
    invoke-static {v1, v2, v3}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;
    move-result-object v0
    invoke-virtual {v0}, Landroid/widget/Toast;->show()V
    :done
    return-void
.end method
