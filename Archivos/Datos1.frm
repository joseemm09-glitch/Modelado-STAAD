VERSION 5.00
Begin {C62A69F0-16DC-11CE-9E98-00AA00574A4F} Datos1 
   Caption         =   "Dosificación para Mezclas de Concreto"
   ClientHeight    =   8148
   ClientLeft      =   120
   ClientTop       =   468
   ClientWidth     =   12000
   OleObjectBlob   =   "Datos1.frx":0000
   StartUpPosition =   2  'CenterScreen
End
Attribute VB_Name = "Datos1"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False


Private Sub CheckBox1_Change()
Sheets("Agua").Select
Range("L19").Select
 If CheckBox1.Value = True Then
 ActiveCell.Value = 1
 End If
  If CheckBox1.Value = False Then
 ActiveCell.Value = 0
 End If
   Sheets("Cemento").Select
  Range("H12").Select
 TextBox3.Value = ActiveCell.Value
End Sub



Private Sub TextBox2_Change()

  Worksheets("Cemento").Range("E7").Value = TextBox2.Value
  Sheets("Cemento").Select
  Range("H12").Select
  TextBox3.Value = ActiveCell.Value
  
End Sub



Private Sub CommandButton3_Click()

Worksheets("Agua").Range("E7").Value = TextBox1.Value

 Sheets("Agua").Select
 Range("E8").Select
 If Agregado.Value = "3/8''  (9.52mm)" Then
 ActiveCell.Value = 10
 End If
 If Agregado.Value = "1/2''  (12.7mm)" Then
 ActiveCell.Value = 13
 End If
 If Agregado.Value = "3/4''  (19.05mm)" Then
 ActiveCell.Value = 20
 End If
 If Agregado.Value = "1''    (25.4mm)" Then
 ActiveCell.Value = 25
 End If
 If Agregado.Value = "1 1/2''(38.1mm)" Then
 ActiveCell.Value = 38
 End If
 If Agregado.Value = "2''   (50.8mm)" Then
 ActiveCell.Value = 50
 End If
 If Agregado.Value = "3''   (76.2mm)" Then
 ActiveCell.Value = 75
 End If
   If Agregado.Value = "6''   (152.4mm)" Then
 ActiveCell.Value = 150
 End If
 Sheets("Agua").Range("L19").Select
 If CheckBox1.Value = True Then
 ActiveCell.Value = 1
 End If
  If CheckBox1.Value = False Then
 ActiveCell.Value = 0
 End If
 
  Worksheets("Cemento").Range("E7").Value = TextBox2.Value
  
  Sheets("Aire").Select
  Range("K7").Select
 If Exposicion.Value = "Baja" Then
 ActiveCell.Value = 0
 End If
 If Exposicion.Value = "Moderada" Then
 ActiveCell.Value = 1
 End If
 If Exposicion.Value = "Severa" Then
 ActiveCell.Value = 2
 End If

 TextBox3.Value = Worksheets("Cemento").Range("H12").Value
 
 Me.Hide
Datos2.Show
End Sub

Private Sub Estructuras_Change()
If Estructuras.Value = "Cimentaciones reforzadas, muros y zapatas" Then
TextBox1.Value = "7.5"
End If
If Estructuras.Value = "Zapatas simples, estribos y muros de subestructura" Then
TextBox1.Value = "7.5"
End If
If Estructuras.Value = "Vigas y muros reforzados" Then
TextBox1.Value = "10"
End If
If Estructuras.Value = "Columnas de edificios" Then
TextBox1.Value = "10"
End If
If Estructuras.Value = "Pavimentos y losas" Then
TextBox1.Value = "7.5"
End If
If Estructuras.Value = "Concreto masivo" Then
TextBox1.Value = "7.5"
End If
End Sub

Private Sub ScrollBar1_Change()
TextBox2.Value = ScrollBar1.Value
End Sub


Private Sub UserForm_Initialize()
Estructuras.AddItem "Cimentaciones reforzadas, muros y zapatas"
Estructuras.AddItem "Zapatas simples, estribos y muros de subestructura"
Estructuras.AddItem "Vigas y muros reforzados"
Estructuras.AddItem "Columnas de edificios"
Estructuras.AddItem "Pavimentos y losas"
Estructuras.AddItem "Concreto masivo"
TextBox2.Value = 250
Agregado.AddItem "3/8''  (9.52mm)"
Agregado.AddItem "1/2''  (12.7mm)"
Agregado.AddItem "3/4''  (19.05mm)"
Agregado.AddItem "1''    (25.4mm)"
Agregado.AddItem "1 1/2''(38.1mm)"
Agregado.AddItem "2''   (50.8mm)"
Agregado.AddItem "3''   (76.2mm)"
Agregado.AddItem "6''   (152.4mm)"
Exposicion.AddItem "Baja"
Exposicion.AddItem "Moderada"
Exposicion.AddItem "Severa"


End Sub

Private Sub UserForm_Terminate()
Me.Hide
Presentacion.Show
End Sub


