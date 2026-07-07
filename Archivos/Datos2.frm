VERSION 5.00
Begin {C62A69F0-16DC-11CE-9E98-00AA00574A4F} Datos2 
   Caption         =   "Dosificación para Mezclas de Concreto"
   ClientHeight    =   7845
   ClientLeft      =   120
   ClientTop       =   468
   ClientWidth     =   11832
   OleObjectBlob   =   "Datos2.frx":0000
   StartUpPosition =   2  'CenterScreen
End
Attribute VB_Name = "Datos2"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Private Sub CommandButton2_Click()
Worksheets("A.Grueso").Range("F7").Value = TextBox16.Value
Worksheets("A.Grueso").Range("H15").Value = TextBox10.Value
Worksheets("A.Grueso").Range("H16").Value = TextBox6.Value
Worksheets("Pesos").Range("G10").Value = TextBox4.Value
Worksheets("Pesos").Range("G13").Value = TextBox12.Value
Worksheets("Corrección").Range("F9").Value = TextBox8.Value
Worksheets("Corrección").Range("H9").Value = TextBox7.Value
Worksheets("Corrección").Range("F10").Value = TextBox14.Value
Worksheets("Corrección").Range("H10").Value = TextBox13.Value
Sheets("Resultado").Select
Me.Hide
Datos3.Show

End Sub

Private Sub UserForm_Terminate()
Me.Hide
Presentacion.Show
End Sub
