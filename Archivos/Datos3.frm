VERSION 5.00
Begin {C62A69F0-16DC-11CE-9E98-00AA00574A4F} Datos3 
   Caption         =   "Dosificación para Mezclas de Concreto"
   ClientHeight    =   7845
   ClientLeft      =   120
   ClientTop       =   468
   ClientWidth     =   11832
   OleObjectBlob   =   "Datos3.frx":0000
   StartUpPosition =   2  'CenterScreen
End
Attribute VB_Name = "Datos3"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False

Private Sub CommandButton2_Click()
Me.Hide
Presentacion.Show

End Sub

Private Sub CommandButton3_Click()
Me.Hide
Application.Visible = True
Sheets("Agua").Select
Range("A1").Select

End Sub




Private Sub UserForm_Activate()
CommandButton2.SetFocus
TextBox4.Text = Worksheets("Resultado").Range("E9").Value
TextBox5.Text = Worksheets("Resultado").Range("E10").Value
TextBox7.Text = Worksheets("Resultado").Range("E11").Value
TextBox8.Text = Worksheets("Resultado").Range("E12").Value
TextBox39.Text = Worksheets("Resultado").Range("E14").Value
TextBox9.Text = Worksheets("Resultado").Range("G9").Value
TextBox11.Text = Worksheets("Resultado").Range("G10").Value
TextBox12.Text = Worksheets("Resultado").Range("G11").Value
TextBox13.Text = Worksheets("Resultado").Range("G12").Value
TextBox40.Text = Worksheets("Resultado").Range("G14").Value
TextBox41.Text = Worksheets("Resultado").Range("I9").Value
TextBox42.Text = Worksheets("Resultado").Range("I10").Value
TextBox43.Text = Worksheets("Resultado").Range("I11").Value
TextBox44.Text = Worksheets("Resultado").Range("I12").Value
TextBox45.Text = Worksheets("Resultado").Range("K9").Value
TextBox46.Text = Worksheets("Resultado").Range("K10").Value
TextBox47.Text = Worksheets("Resultado").Range("K11").Value
TextBox48.Text = Worksheets("Resultado").Range("K12").Value
TextBox50.Text = Worksheets("Resultado").Range("M9").Value
TextBox51.Text = Worksheets("Resultado").Range("M10").Value
TextBox52.Text = Worksheets("Resultado").Range("M11").Value
TextBox49.Text = Worksheets("Resultado").Range("M12").Value
TextBox53.Text = Worksheets("Resultado").Range("N9").Value
TextBox55.Text = Worksheets("Resultado").Range("N10").Value
TextBox56.Text = Worksheets("Resultado").Range("N11").Value
TextBox54.Text = Worksheets("Resultado").Range("N12").Value
CommandButton2.SetFocus

End Sub

Private Sub UserForm_Terminate()
Me.Hide
Presentacion.Show
End Sub


