Attribute VB_Name = "Módulo1"
Option Explicit

' === Texto / Formato ===
Public Function WrapLine(ByVal sLine As String, ByVal maxLen As Integer) As String
    Dim result As String, pos As Integer
    result = ""
    Do While Len(sLine) > maxLen
        pos = InStrRev(Left$(sLine, maxLen), " ")
        If pos = 0 Then pos = maxLen
        result = result & Left$(sLine, pos) & vbCrLf
        sLine = Trim$(Mid$(sLine, pos + 1))
    Loop
    WrapLine = result & sLine
End Function

Public Function WrapAllLines(ByVal textBlock As String, ByVal maxLen As Integer) As String
    Dim lines() As String, i As Long, wrappedText As String
    lines = Split(textBlock, vbCrLf)
    wrappedText = ""
    For i = LBound(lines) To UBound(lines)
        wrappedText = wrappedText & WrapLine(lines(i), maxLen) & vbCrLf
    Next i
    If Len(wrappedText) > 0 Then wrappedText = Left$(wrappedText, Len(wrappedText) - 2)
    WrapAllLines = wrappedText
End Function

' === Agrupar rangos "1 2 3 7 8 10" ? "1 TO 3 7 8 10" ===
Public Function GroupRanges(ByRef numbers() As Long, ByVal numCount As Long) As String
    Dim tmp() As Long, i As Long, n As Long
    If numCount <= 0 Then Exit Function
    
    ' Copiar no-cero
    ReDim tmp(1 To numCount)
    For i = 1 To numCount
        If numbers(i) <> 0 Then
            n = n + 1
            tmp(n) = numbers(i)
        End If
    Next i
    If n = 0 Then Exit Function
    If n < numCount Then ReDim Preserve tmp(1 To n)
    
    ' Ordenar (burbuja rápida para n chico; si lo quieres, cambia a QuickSort)
    Dim swapped As Boolean, j As Long
    Do
        swapped = False
        For j = 1 To n - 1
            If tmp(j) > tmp(j + 1) Then
                i = tmp(j): tmp(j) = tmp(j + 1): tmp(j + 1) = i
                swapped = True
            End If
        Next j
    Loop While swapped
    
    ' Compactar
    Dim startNum As Long, endNum As Long, grp As String
    startNum = tmp(1): endNum = tmp(1)
    For i = 2 To n
        If tmp(i) = endNum + 1 Then
            endNum = tmp(i)
        Else
            If startNum = endNum Then
                grp = grp & startNum & " "
            Else
                grp = grp & startNum & " TO " & endNum & " "
            End If
            startNum = tmp(i): endNum = tmp(i)
        End If
    Next i
    If startNum = endNum Then
        grp = grp & startNum
    Else
        grp = grp & startNum & " TO " & endNum
    End If
    GroupRanges = Trim$(grp)
End Function

' === Volcado rápido a hojas ===
Public Sub RellenarTablaNodes(ByVal nodeData As String)
    Dim ws As Worksheet, lines() As String, parts() As String
    Dim r As Long, i As Long
    On Error Resume Next
    Set ws = ThisWorkbook.Worksheets("Nodes")
    On Error GoTo 0
    If ws Is Nothing Then
        Set ws = ThisWorkbook.Worksheets.Add(After:=ThisWorkbook.Sheets(ThisWorkbook.Sheets.count))
        ws.Name = "Nodes"
    Else
        ws.Cells.Clear
    End If
    
    lines = Split(nodeData, vbCrLf)
    ' Filtrar vacíos
    Dim count As Long
    For i = LBound(lines) To UBound(lines)
        If Len(Trim$(lines(i))) > 0 Then count = count + 1
    Next i
    If count = 0 Then Exit Sub
    
    Dim arr(): ReDim arr(1 To count, 1 To 4)
    r = 0
    For i = LBound(lines) To UBound(lines)
        If Len(Trim$(lines(i))) > 0 Then
            parts = Split(Trim$(lines(i)))
            r = r + 1
            arr(r, 1) = CLng(parts(0))
            arr(r, 2) = CDbl(parts(1))
            arr(r, 3) = CDbl(parts(2))
            arr(r, 4) = CDbl(parts(3))
        End If
    Next i
    
    ws.Range("A1:D1").Value = Array("Node", "X", "Y", "Z")
    ws.Range("A2").Resize(count, 4).Value = arr
    ws.Columns("A:D").AutoFit
End Sub

Public Sub RellenarTablaMembers(ByVal memberData As String)
    Dim ws As Worksheet, lines() As String, parts() As String
    Dim r As Long, i As Long
    On Error Resume Next
    Set ws = ThisWorkbook.Worksheets("Members")
    On Error GoTo 0
    If ws Is Nothing Then
        Set ws = ThisWorkbook.Worksheets.Add(After:=ThisWorkbook.Sheets(ThisWorkbook.Sheets.count))
        ws.Name = "Members"
    Else
        ws.Cells.Clear
    End If
    
    lines = Split(memberData, vbCrLf)
    Dim count As Long
    For i = LBound(lines) To UBound(lines)
        If Len(Trim$(lines(i))) > 0 Then count = count + 1
    Next i
    If count = 0 Then Exit Sub
    
    Dim arr(): ReDim arr(1 To count, 1 To 3)
    r = 0
    For i = LBound(lines) To UBound(lines)
        If Len(Trim$(lines(i))) > 0 Then
            parts = Split(Trim$(lines(i)))
            r = r + 1
            arr(r, 1) = CLng(parts(0))
            arr(r, 2) = CLng(parts(1))
            arr(r, 3) = CLng(parts(2))
        End If
    Next i
    
    ws.Range("A1:C1").Value = Array("Member", "Node I", "Node J")
    ws.Range("A2").Resize(count, 3).Value = arr
    ws.Columns("A:C").AutoFit
End Sub

