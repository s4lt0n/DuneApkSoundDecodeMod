.class public final Lcom/dunehd/shell/settings/DtsPcmSettings$Choice;
.super Ljava/lang/Object;
.implements Landroid/content/DialogInterface$OnMultiChoiceClickListener;
.field private final context:Landroid/content/Context;

.method public constructor <init>(Landroid/content/Context;)V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Lcom/dunehd/shell/settings/DtsPcmSettings$Choice;->context:Landroid/content/Context;
    return-void
.end method

.method public onClick(Landroid/content/DialogInterface;IZ)V
    .locals 3
    invoke-static {p3}, Lcom/dunehd/shell/settings/DtsPcmSettings;->save(Z)Z
    move-result v0
    if-nez v0, :done
    check-cast p1, Landroid/app/AlertDialog;
    invoke-virtual {p1}, Landroid/app/AlertDialog;->getListView()Landroid/widget/ListView;
    move-result-object v0
    xor-int/lit8 v1, p3, 0x1
    invoke-virtual {v0, p2, v1}, Landroid/widget/ListView;->setItemChecked(IZ)V
    iget-object v0, p0, Lcom/dunehd/shell/settings/DtsPcmSettings$Choice;->context:Landroid/content/Context;
    const-string v1, "dts_pcm_save_error"
    invoke-static {v0, v1}, Lcom/dunehd/shell/settings/DtsPcmSettings;->text(Landroid/content/Context;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v1
    const/4 v2, 0x1
    invoke-static {v0, v1, v2}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;
    move-result-object v0
    invoke-virtual {v0}, Landroid/widget/Toast;->show()V
    :done
    return-void
.end method
