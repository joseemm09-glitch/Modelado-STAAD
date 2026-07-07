Attribute VB_Name = "Módulo2"
Option Explicit

' ==== Helper: ID de nodo superior en el índice k del claro ====
' k = 0              ? nL3(i,j)
' 1..numSubdiv-1     ? upperSub(i,j,k)
' k = numSubdiv      ? nL3(i,j+1)
Private Function UpperNodeID( _
    ByRef nL3() As Long, _
    ByRef upperSub() As Long, _
    ByVal i As Long, ByVal j As Long, _
    ByVal k As Long, ByVal numSubdiv As Long) As Long

    If k = 0 Then
        UpperNodeID = nL3(i, j)
    ElseIf k = numSubdiv Then
        UpperNodeID = nL3(i, j + 1)
    Else
        UpperNodeID = upperSub(i, j, k)
    End If
End Function

' ===== Generador completo (con Montantes, Diagonales y Largueros) =====
Public Sub GenerarModeloSTAAD( _
    ByVal longitudArmaduras_m As Double, _
    ByVal longitudJoists_m As Double, _
    ByVal numeroBahias As Long, _
    ByVal numeroEntreEjes As Long, _
    ByVal alturaArmadura_m As Double, _
    ByVal alturaLibre_m As Double, _
    ByVal numSubdiv As Long)

    ' --- Validaciones ---
    If longitudArmaduras_m <= 0 Or longitudJoists_m <= 0 Then Err.Raise 5, , "Longitudes > 0"
    If numeroBahias < 0 Or numeroEntreEjes < 1 Then Err.Raise 5, , "Bahías = 0 y Entre-ejes = 1"
    If alturaArmadura_m <= 0 Or alturaLibre_m <= 0 Then Err.Raise 5, , "Alturas > 0"
    If numSubdiv < 2 Or (numSubdiv Mod 2) <> 0 Then Err.Raise 5, , "NumSubdiv debe ser par y = 2"

    ' --- Unidades a cm ---
    Dim Lx As Double, Lz As Double, HtArmad As Double, HtLibre As Double
    Lx = longitudArmaduras_m * 100#
    Lz = longitudJoists_m * 100#
    HtArmad = alturaArmadura_m * 100#
    HtLibre = alturaLibre_m * 100#

    Dim nBay As Long, nSpan As Long, nGrid As Long
    nBay = numeroBahias
    nSpan = numeroEntreEjes
    nGrid = (nBay + 1) * (nSpan + 1)

    Dim halfSub As Long: halfSub = numSubdiv \ 2
    Dim nUpperInter As Long: nUpperInter = (nBay + 1) * nSpan * (numSubdiv - 1)
    Dim nLowerInter As Long: nLowerInter = (nBay + 1) * nSpan * halfSub

    ' --- Conteos ---
    Dim totalNodes As Long
    totalNodes = 3 * nGrid + nUpperInter + nLowerInter

    Dim mCols As Long, mUpper As Long, mLower As Long, mMonts As Long, mDiag As Long, mLarg As Long
    mCols = 2 * nGrid
    mUpper = (nBay + 1) * nSpan * numSubdiv
    mLower = (nBay + 1) * nSpan * (halfSub + 1)
    mMonts = nLowerInter
    mDiag = (nBay + 1) * nSpan * numSubdiv           ' 2*halfSub por claro
    mLarg = nBay * (nSpan * numSubdiv + 1)           ' nodos en X: (nSpan+1) + nSpan*(numSubdiv-1)

    Dim totalMembers As Long
    totalMembers = mCols + mUpper + mLower + mMonts + mDiag + mLarg

    ' --- Buffers ---
    Dim nodeLines() As String, memberLines() As String
    ReDim nodeLines(1 To totalNodes)
    ReDim memberLines(1 To totalMembers)
    Dim nodePtr As Long: nodePtr = 0
    Dim membPtr As Long: membPtr = 0

    ' --- Índices / Grupos ---
    Dim nodeID As Long: nodeID = 0
    Dim memID As Long: memID = 0

    Dim GRP_COL() As Long, GRP_CS() As Long, GRP_CI() As Long, GRP_MONT() As Long, GRP_DIAG() As Long, GRP_LARG() As Long
    ReDim GRP_COL(1 To mCols)
    ReDim GRP_CS(1 To mUpper)
    ReDim GRP_CI(1 To mLower)
    ReDim GRP_MONT(1 To mMonts)
    ReDim GRP_DIAG(1 To mDiag)
    If mLarg > 0 Then ReDim GRP_LARG(1 To mLarg) Else ReDim GRP_LARG(1 To 1) ' seguro para 0
    Dim iCOL As Long, iCS As Long, iCI As Long, iM As Long, iDG As Long, iLG As Long
    iCOL = 0: iCS = 0: iCI = 0: iM = 0: iDG = 0: iLG = 0

    ' --- Mapas de nodos ---
    Dim nL1() As Long, nL2() As Long, nL3() As Long
    ReDim nL1(0 To nBay, 0 To nSpan)
    ReDim nL2(0 To nBay, 0 To nSpan)
    ReDim nL3(0 To nBay, 0 To nSpan)

    ' upperSub(bay, span, k=1..numSubdiv-1)
    Dim upperSub() As Long
    ReDim upperSub(0 To nBay, 0 To nSpan - 1, 1 To numSubdiv - 1)

    ' lowerInter(bay, span, t=1..halfSub)
    Dim lowerInter() As Long
    ReDim lowerInter(0 To nBay, 0 To nSpan - 1, 1 To halfSub)

    ' --- Crear nodos ---
    Dim i As Long, j As Long, k As Long, t As Long
    Dim x As Double, y As Double, z As Double

    ' Nivel 1
    For j = 0 To nSpan
        For i = 0 To nBay
            x = j * Lx: y = 0#: z = i * Lz
            nodeID = nodeID + 1: nodePtr = nodePtr + 1
            nodeLines(nodePtr) = CStr(nodeID) & " " & Format$(x, "0.00") & " " & Format$(y, "0.00") & " " & Format$(z, "0.00")
            nL1(i, j) = nodeID
        Next i
    Next j

    ' Nivel 2
    For j = 0 To nSpan
        For i = 0 To nBay
            x = j * Lx: y = HtLibre: z = i * Lz
            nodeID = nodeID + 1: nodePtr = nodePtr + 1
            nodeLines(nodePtr) = CStr(nodeID) & " " & Format$(x, "0.00") & " " & Format$(y, "0.00") & " " & Format$(z, "0.00")
            nL2(i, j) = nodeID
        Next i
    Next j

    ' Nivel 3
    For j = 0 To nSpan
        For i = 0 To nBay
            x = j * Lx: y = HtLibre + HtArmad: z = i * Lz
            nodeID = nodeID + 1: nodePtr = nodePtr + 1
            nodeLines(nodePtr) = CStr(nodeID) & " " & Format$(x, "0.00") & " " & Format$(y, "0.00") & " " & Format$(z, "0.00")
            nL3(i, j) = nodeID
        Next i
    Next j

    ' --- Miembros ---

    ' Columnas
    For j = 0 To nSpan
        For i = 0 To nBay
            memID = memID + 1: membPtr = membPtr + 1
            memberLines(membPtr) = CStr(memID) & " " & nL1(i, j) & " " & nL2(i, j)
            iCOL = iCOL + 1: GRP_COL(iCOL) = memID

            memID = memID + 1: membPtr = membPtr + 1
            memberLines(membPtr) = CStr(memID) & " " & nL2(i, j) & " " & nL3(i, j)
            iCOL = iCOL + 1: GRP_COL(iCOL) = memID
        Next i
    Next j

    ' Cuerda superior (nivel 3)
    Dim x0 As Double, x1 As Double, y3 As Double, z0 As Double
    y3 = HtLibre + HtArmad
    For i = 0 To nBay
        For j = 0 To nSpan - 1
            x0 = j * Lx: x1 = (j + 1) * Lx: z0 = i * Lz
            Dim prev As Long: prev = nL3(i, j)
            For k = 1 To numSubdiv - 1
                Dim xn As Double: xn = x0 + (x1 - x0) * (k / numSubdiv)
                nodeID = nodeID + 1: nodePtr = nodePtr + 1
                nodeLines(nodePtr) = CStr(nodeID) & " " & Format$(xn, "0.00") & " " & Format$(y3, "0.00") & " " & Format$(z0, "0.00")
                upperSub(i, j, k) = nodeID

                memID = memID + 1: membPtr = membPtr + 1
                memberLines(membPtr) = CStr(memID) & " " & prev & " " & nodeID
                iCS = iCS + 1: GRP_CS(iCS) = memID
                prev = nodeID
            Next k
            memID = memID + 1: membPtr = membPtr + 1
            memberLines(membPtr) = CStr(memID) & " " & prev & " " & nL3(i, j + 1)
            iCS = iCS + 1: GRP_CS(iCS) = memID
        Next j
    Next i

    ' Cuerda inferior (nivel 2)
    Dim L0 As Double: L0 = Lx / numSubdiv
    Dim oddK As Long
    For i = 0 To nBay
        For j = 0 To nSpan - 1
            Dim baseX As Double: baseX = j * Lx
            Dim z2 As Double: z2 = i * Lz
            Dim leftN As Long: leftN = nL2(i, j)

            For t = 1 To halfSub
                oddK = 2 * t - 1
                x = baseX + oddK * L0
                nodeID = nodeID + 1: nodePtr = nodePtr + 1
                nodeLines(nodePtr) = CStr(nodeID) & " " & Format$(x, "0.00") & " " & Format$(HtLibre, "0.00") & " " & Format$(z2, "0.00")
                lowerInter(i, j, t) = nodeID

                memID = memID + 1: membPtr = membPtr + 1
                memberLines(membPtr) = CStr(memID) & " " & leftN & " " & nodeID
                iCI = iCI + 1: GRP_CI(iCI) = memID
                leftN = nodeID
            Next t

            memID = memID + 1: membPtr = membPtr + 1
            memberLines(membPtr) = CStr(memID) & " " & leftN & " " & nL2(i, j + 1)
            iCI = iCI + 1: GRP_CI(iCI) = memID
        Next j
    Next i

    ' Montantes
    For i = 0 To nBay
        For j = 0 To nSpan - 1
            For t = 1 To halfSub
                oddK = 2 * t - 1
                memID = memID + 1: membPtr = membPtr + 1
                memberLines(membPtr) = CStr(memID) & " " & lowerInter(i, j, t) & " " & upperSub(i, j, oddK)
                iM = iM + 1: GRP_MONT(iM) = memID
            Next t
        Next j
    Next i

    ' Diagonales (en "V")
    For i = 0 To nBay
        For j = 0 To nSpan - 1
            For t = 1 To halfSub
                ' izquierda
                memID = memID + 1: membPtr = membPtr + 1
                memberLines(membPtr) = CStr(memID) & " " & _
                    UpperNodeID(nL3, upperSub, i, j, 2 * (t - 1), numSubdiv) & " " & _
                    lowerInter(i, j, t)
                iDG = iDG + 1: GRP_DIAG(iDG) = memID
                ' derecha
                memID = memID + 1: membPtr = membPtr + 1
                memberLines(membPtr) = CStr(memID) & " " & _
                    UpperNodeID(nL3, upperSub, i, j, 2 * t, numSubdiv) & " " & _
                    lowerInter(i, j, t)
                iDG = iDG + 1: GRP_DIAG(iDG) = memID
            Next t
        Next j
    Next i

    ' Largueros (nivel 3, dirección Z)
    If nBay >= 1 Then
        ' En nodos extremos de cada claro (j = 0..nSpan)
        For j = 0 To nSpan
            For i = 0 To nBay - 1
                memID = memID + 1: membPtr = membPtr + 1
                memberLines(membPtr) = CStr(memID) & " " & nL3(i, j) & " " & nL3(i + 1, j)
                iLG = iLG + 1: GRP_LARG(iLG) = memID
            Next i
        Next j
        ' En todos los nodos intermedios superiores (k = 1..numSubdiv-1)
        For j = 0 To nSpan - 1
            For k = 1 To numSubdiv - 1
                For i = 0 To nBay - 1
                    memID = memID + 1: membPtr = membPtr + 1
                    memberLines(membPtr) = CStr(memID) & " " & upperSub(i, j, k) & " " & upperSub(i + 1, j, k)
                    iLG = iLG + 1: GRP_LARG(iLG) = memID
                Next i
            Next k
        Next j
    End If

    ' --- Empaquetar STAAD ---
    Dim staadText As String
    Dim engineerDate As String: engineerDate = Format$(Date, "dd-mmm-yy")

    staadText = ""
    staadText = staadText & "STAAD SPACE" & vbCrLf
    staadText = staadText & "START JOB INFORMATION" & vbCrLf
    staadText = staadText & "ENGINEER DATE " & engineerDate & vbCrLf
    staadText = staadText & "END JOB INFORMATION" & vbCrLf
    staadText = staadText & "INPUT WIDTH 79" & vbCrLf
    staadText = staadText & "UNIT CM KG" & vbCrLf & vbCrLf

    staadText = staadText & "JOINT COORDINATES" & vbCrLf
    staadText = staadText & Join(nodeLines, vbCrLf) & vbCrLf & ";" & vbCrLf & vbCrLf

    staadText = staadText & "MEMBER INCIDENCES" & vbCrLf
    staadText = staadText & Join(memberLines, vbCrLf) & vbCrLf & ";" & vbCrLf & vbCrLf

    ' --- Grupos ---
    Dim colStr As String, csStr As String, ciStr As String, montStr As String, diagStr As String, largStr As String
    colStr = GroupRanges(GRP_COL, iCOL)
    csStr = GroupRanges(GRP_CS, iCS)
    ciStr = GroupRanges(GRP_CI, iCI)
    montStr = GroupRanges(GRP_MONT, iM)
    diagStr = GroupRanges(GRP_DIAG, iDG)
    largStr = GroupRanges(GRP_LARG, iLG)

    staadText = staadText & "START GROUP DEFINITION" & vbCrLf & "MEMBER" & vbCrLf
    If Len(colStr) > 0 Then staadText = staadText & "_COL " & colStr & vbCrLf
    If Len(csStr) > 0 Then staadText = staadText & "_CS " & csStr & vbCrLf
    If Len(ciStr) > 0 Then staadText = staadText & "_CI " & ciStr & vbCrLf
    If Len(montStr) > 0 Then staadText = staadText & "_MONTANTES " & montStr & vbCrLf
    If Len(diagStr) > 0 Then staadText = staadText & "_DIAG " & diagStr & vbCrLf
    If Len(largStr) > 0 Then staadText = staadText & "_LARGUEROS " & largStr & vbCrLf
    staadText = staadText & "END GROUP DEFINITION" & vbCrLf & vbCrLf
    staadText = staadText & "FINISH"

    ' Ancho de línea opcional
    staadText = WrapAllLines(staadText, 72)

    ' --- Guardar .std ---
    Dim fName As Variant, ff As Integer
    fName = Application.GetSaveAsFilename(InitialFileName:="Modelo_STAAD.std", _
                                          fileFilter:="STAAD Files (*.std), *.std")
    If fName = False Then
        MsgBox "Operación cancelada.", vbExclamation
        Exit Sub
    End If
    ff = FreeFile: Open CStr(fName) For Output As #ff: Print #ff, staadText: Close #ff

    ' --- Volcado a Excel ---
    Call RellenarTablaNodes(Join(nodeLines, vbCrLf))
    Call RellenarTablaMembers(Join(memberLines, vbCrLf))
    
    ff = FreeFile
    Open CStr(fName) For Output As #ff
    Print #ff, staadText
    Close #ff
    
    Call RellenarTablaNodes(Join(nodeLines, vbCrLf))
    Call RellenarTablaMembers(Join(memberLines, vbCrLf))
    
    ' Abre el .std en STAAD
    Call AbrirSTDEnSTAAD(CStr(fName))
    
    'MsgBox "Archivo STAAD generado:" & vbCrLf & CStr(fName), vbInformation
End Sub

' ===== Puente para el UserForm (sin cambios) =====
Public Sub EjecutarDesdeFormulario( _
    ByVal txt1 As String, ByVal txt2 As String, ByVal txt3 As String, _
    ByVal txt4 As String, ByVal txt5 As String, ByVal txt6 As String, ByVal txt7 As String)

    Dim Larm_m As Double, Ljoist_m As Double
    Dim nBay As Long, nSpan As Long
    Dim HArmad_m As Double, HLibre_m As Double
    Dim subdiv As Long

    If IsNumeric(txt1) Then Larm_m = CDbl(txt1) Else Err.Raise 5, , "Longitud de Armaduras inválida"
    If IsNumeric(txt2) Then Ljoist_m = CDbl(txt2) Else Err.Raise 5, , "Longitud de Joists inválida"
    If IsNumeric(txt3) Then nBay = CLng(txt3) Else Err.Raise 5, , "Número de Bahías inválido"
    If IsNumeric(txt4) Then nSpan = CLng(txt4) Else Err.Raise 5, , "Número de Entre-ejes inválido"
    If IsNumeric(txt5) Then HArmad_m = CDbl(txt5) Else Err.Raise 5, , "Altura de armadura inválida"
    If IsNumeric(txt6) Then HLibre_m = CDbl(txt6) Else Err.Raise 5, , "Altura libre inválida"
    If IsNumeric(txt7) Then subdiv = CLng(txt7) Else Err.Raise 5, , "Separaciones/Subdivisiones inválidas"

    Application.ScreenUpdating = False
    On Error GoTo EH
    Call GenerarModeloSTAAD(Larm_m, Ljoist_m, nBay, nSpan, HArmad_m, HLibre_m, subdiv)
    Application.ScreenUpdating = True
    Exit Sub
EH:
    Application.ScreenUpdating = True
    MsgBox "Error: " & Err.Description, vbCritical
End Sub

