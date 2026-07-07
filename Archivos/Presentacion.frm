VERSION 5.00
Begin {C62A69F0-16DC-11CE-9E98-00AA00574A4F} Presentacion 
   Caption         =   "Entrada de Datos"
   ClientHeight    =   7320
   ClientLeft      =   120
   ClientTop       =   468
   ClientWidth     =   11760
   OleObjectBlob   =   "Presentacion.frx":0000
   StartUpPosition =   2  'CenterScreen
End
Attribute VB_Name = "Presentacion"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Private Sub CommandButton1_Click()
    ' Llama al generador con los TextBox (1..7) del formulario
    Call EjecutarDesdeFormulario( _
        Me.TextBox1.Text, Me.TextBox2.Text, Me.TextBox3.Text, _
        Me.TextBox4.Text, Me.TextBox5.Text, Me.TextBox6.Text, Me.TextBox7.Text)
End Sub

Private Sub CommandButton2_Click()
    On Error Resume Next
    ' Asegura que Excel esté visible y restaurado
    Application.Visible = True
    Application.WindowState = xlNormal
    Application.DisplayFullScreen = False

    ' Trae al frente este libro
    ThisWorkbook.Activate

    ' Cierra el formulario
    Unload Me
End Sub

Private Sub TextBox7_Change()
    Dim num1 As Double
    Dim num2 As Double
    Dim resultado As Double
    
    If IsNumeric(TextBox1.Value) And IsNumeric(TextBox7.Value) Then
        num1 = CDbl(TextBox1.Value)
        num2 = CDbl(TextBox7.Value)
        
        If num2 <> 0 Then
            resultado = num1 / num2
            Label14.Caption = "(" & Format(resultado, "0.000") & " m)"
        Else
            Label14.Caption = "(Div/0!)"
        End If
    Else
        Label14.Caption = ""
    End If
End Sub

Private Sub TextBox1_Change()
    Dim num1 As Double
    Dim num2 As Double
    Dim resultado As Double
    
    If IsNumeric(TextBox1.Value) And IsNumeric(TextBox7.Value) Then
        num1 = CDbl(TextBox1.Value)
        num2 = CDbl(TextBox7.Value)
        
        If num2 <> 0 Then
            resultado = num1 / num2
            Label14.Caption = "(" & Format(resultado, "0.000") & " m)"
        Else
            Label14.Caption = "(Div/0!)"
        End If
    Else
        Label14.Caption = ""
    End If
End Sub

' Opcional: seleccionar todo al hacer click en cada textbox (como ya tenías)
Private Sub TextBox1_Enter(): Me.TextBox1.SelStart = 0: Me.TextBox1.SelLength = Len(Me.TextBox1.Text): End Sub
Private Sub TextBox2_Enter(): Me.TextBox2.SelStart = 0: Me.TextBox2.SelLength = Len(Me.TextBox2.Text): End Sub
Private Sub TextBox3_Enter(): Me.TextBox3.SelStart = 0: Me.TextBox3.SelLength = Len(Me.TextBox3.Text): End Sub
Private Sub TextBox4_Enter(): Me.TextBox4.SelStart = 0: Me.TextBox4.SelLength = Len(Me.TextBox4.Text): End Sub
Private Sub TextBox5_Enter(): Me.TextBox5.SelStart = 0: Me.TextBox5.SelLength = Len(Me.TextBox5.Text): End Sub
Private Sub TextBox6_Enter(): Me.TextBox6.SelStart = 0: Me.TextBox6.SelLength = Len(Me.TextBox6.Text): End Sub
Private Sub TextBox7_Enter(): Me.TextBox7.SelStart = 0: Me.TextBox7.SelLength = Len(Me.TextBox7.Text): End Sub


Private Sub UserForm_Click()

End Sub
