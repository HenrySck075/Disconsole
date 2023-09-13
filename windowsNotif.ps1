$ErrorActionPreference = "Stop"
$notificationTitle = $args[0]
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText01)
$toastXml = [xml] $template.GetXml()
$toastXml.GetElementsByTagName("text").AppendChild($toastXml.CreateTextNode($notificationTitle)) > $null
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($toastXml.OuterXml)
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
$toast.Tag = "meow"
$toast.Group = $args[2]
$toast.ExpirationTime = [DateTimeOffset]::Now.AddSeconds(5)
$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($args[1])
$notifier.Show($toast);
