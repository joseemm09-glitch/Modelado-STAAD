Attribute VB_Name = "Module1"
Option Explicit

#If VBA7 Then
Private Declare PtrSafe Function ShellExecute Lib "shell32.dll" Alias "ShellExecuteA" ( _
    ByVal hwnd As LongPtr, ByVal lpOperation As String, ByVal lpFile As String, _
    ByVal lpParameters As String, ByVal lpDirectory As String, ByVal nShowCmd As Long) As LongPtr
#Else
Private Declare Function ShellExecute Lib "shell32.dll" Alias "ShellExecuteA" ( _
    ByVal hwnd As Long, ByVal lpOperation As String, ByVal lpFile As String, _
    ByVal lpParameters As String, ByVal lpDirectory As String, ByVal nShowCmd As Long) As Long
#End If

' Abre el archivo con la aplicación predeterminada en Windows (.std ? STAAD)
Public Sub AbrirSTDEnSTAAD(ByVal fPath As String)
    Dim ret As LongPtr
    On Error Resume Next
    ret = ShellExecute(0, "open", fPath, vbNullString, vbNullString, 1)
    ' Fallback por si la asociación tarda o falla
    If ret <= 32 Then
        Shell "cmd /c start """" " & Chr$(34) & fPath & Chr$(34), vbHide
    End If
End Sub


