.class public final Lcom/dunehd/shell/settings/DtsPcmSettings;
.super Ljava/lang/Object;

.method private static flagFile()Ljava/io/File;
    .locals 2
    new-instance v0, Lcom/dunehd/shell/FSFile;
    const-string v1, "/config/decode_dts_pcm"
    invoke-direct {v0, v1}, Lcom/dunehd/shell/FSFile;-><init>(Ljava/lang/String;)V
    invoke-virtual {v0}, Lcom/dunehd/shell/FSFile;->getFile()Ljava/io/File;
    move-result-object v0
    return-object v0
.end method

.method public static isEnabled()Z
    .locals 1
    :try_start
    invoke-static {}, Lcom/dunehd/shell/settings/DtsPcmSettings;->flagFile()Ljava/io/File;
    move-result-object v0
    invoke-virtual {v0}, Ljava/io/File;->isFile()Z
    move-result v0
    :try_end
    return v0
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :failure
    :failure
    move-exception v0
    const/4 v0, 0x0
    return v0
.end method

.method public static filterMask(I)I
    .locals 1
    invoke-static {}, Lcom/dunehd/shell/settings/DtsPcmSettings;->isEnabled()Z
    move-result v0
    if-eqz v0, :done
    and-int/lit16 p0, p0, -0x181
    :done
    return p0
.end method

.method public static save(Z)Z
    .locals 3
    :try_start
    invoke-static {}, Lcom/dunehd/shell/settings/DtsPcmSettings;->flagFile()Ljava/io/File;
    move-result-object v0
    if-eqz p0, :disable
    invoke-virtual {v0}, Ljava/io/File;->getParentFile()Ljava/io/File;
    move-result-object v1
    invoke-virtual {v1}, Ljava/io/File;->mkdirs()Z
    invoke-virtual {v0}, Ljava/io/File;->createNewFile()Z
    invoke-virtual {v0}, Ljava/io/File;->isFile()Z
    move-result v0
    return v0
    :disable
    invoke-virtual {v0}, Ljava/io/File;->exists()Z
    move-result v1
    if-eqz v1, :success
    invoke-virtual {v0}, Ljava/io/File;->delete()Z
    move-result v0
    return v0
    :success
    const/4 v0, 0x1
    :try_end
    return v0
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :failure
    :failure
    move-exception v0
    const-string v1, "DtsPcmSettings"
    const-string v2, "Could not persist DTS PCM preference"
    invoke-static {v1, v2, v0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I
    const/4 v0, 0x0
    return v0
.end method

.method public static text(Landroid/content/Context;Ljava/lang/String;)Ljava/lang/String;
    .locals 3
    invoke-virtual {p0}, Landroid/content/Context;->getResources()Landroid/content/res/Resources;
    move-result-object v0
    const-string v1, "string"
    invoke-virtual {p0}, Landroid/content/Context;->getPackageName()Ljava/lang/String;
    move-result-object v2
    invoke-virtual {v0, p1, v1, v2}, Landroid/content/res/Resources;->getIdentifier(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)I
    move-result v0
    invoke-virtual {p0, v0}, Landroid/content/Context;->getString(I)Ljava/lang/String;
    move-result-object v0
    return-object v0
.end method

.method public static show(Landroid/app/Activity;)Z
    .locals 2
    if-eqz p0, :failure
    :try_start
    new-instance v0, Lcom/dunehd/shell/settings/DtsPcmSettings$ShowDialog;
    invoke-direct {v0, p0}, Lcom/dunehd/shell/settings/DtsPcmSettings$ShowDialog;-><init>(Landroid/app/Activity;)V
    invoke-virtual {p0, v0}, Landroid/app/Activity;->runOnUiThread(Ljava/lang/Runnable;)V
    :try_end
    const/4 v0, 0x1
    return v0
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :error
    :error
    move-exception v0
    const-string v1, "DtsPcmSettings"
    invoke-static {v1, v1, v0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I
    :failure
    const/4 v0, 0x0
    return v0
.end method
