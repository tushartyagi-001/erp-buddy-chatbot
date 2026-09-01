/*
    ERP Buddy Chatbot — READ ONLY fee procedures
    File: USP_ChatBot_FeeTools.sql
    Safe deploy: CREATE OR ALTER only — existing ERP procedures / tables unchanged.
    Run once on SQL Server when enabling chatbot fee tools.
*/

SET NOCOUNT ON;
GO

CREATE OR ALTER PROCEDURE dbo.USP_ChatBot_FeeSearchStudent
(
    @SearchText NVARCHAR(150),
    @BranchId INT,
    @OrgId INT = 0,
    @PageSize INT = 15
)
AS
BEGIN
    SET NOCOUNT ON;
    SET @SearchText = LTRIM(RTRIM(ISNULL(@SearchText, '')));
    IF LEN(@SearchText) < 2 RETURN;
    IF @PageSize IS NULL OR @PageSize <= 0 SET @PageSize = 15;
    IF @PageSize > 25 SET @PageSize = 25;

    SELECT TOP (@PageSize)
        A.StudentFeeAssignmentId,
        TRY_CAST(A.StudentRegNo AS BIGINT) AS StudentRegNo,
        A.StudentName,
        ISNULL(CM.CourseName, '') AS CourseName,
        ISNULL(A.BatchName, CB.BatchName) AS BatchName,
        A.StructureName AS FeeStructureName,
        A.GrandTotal,
        A.PaidAmount,
        A.BalanceAmount,
        CASE
            WHEN ISNULL(A.GrandTotal, 0) <= 0 THEN 'Assigned'
            WHEN ISNULL(A.BalanceAmount, 0) <= 0 THEN 'Paid'
            WHEN ISNULL(A.PaidAmount, 0) > 0 THEN 'Partial'
            ELSE 'Pending'
        END AS FeeStatus
    FROM dbo.Tbl_StudentFeeAssignment A
    LEFT JOIN dbo.Tbl_CourseMaster CM ON CM.CourseId = A.CourseId
    LEFT JOIN dbo.Tbl_CourseBatch CB ON CB.BatchId = A.BatchId
    WHERE A.BranchId = @BranchId
      AND (@OrgId = 0 OR A.OrganizationId = @OrgId)
      AND ISNULL(A.Status, '') <> 'Closed'
      AND (
          A.StudentName LIKE '%' + @SearchText + '%'
          OR A.StudentRegNo LIKE '%' + @SearchText + '%'
          OR CAST(A.StudentId AS NVARCHAR(30)) = @SearchText
      )
    ORDER BY A.BalanceAmount DESC, A.StudentName;
END
GO

CREATE OR ALTER PROCEDURE dbo.USP_ChatBot_StudentFeeInstallments
(
    @StudentRegNo BIGINT,
    @BranchId INT,
    @OrgId INT = 0
)
AS
BEGIN
    SET NOCOUNT ON;

    SELECT TOP 60
        A.StudentFeeAssignmentId,
        TRY_CAST(A.StudentRegNo AS BIGINT) AS StudentRegNo,
        A.StudentName,
        ISNULL(CM.CourseName, '') AS CourseName,
        A.StructureName AS FeeStructureName,
        A.GrandTotal,
        A.PaidAmount,
        A.BalanceAmount,
        I.FeeHeadName,
        I.InstallmentNo,
        CONVERT(VARCHAR(10), I.DueDate, 120) AS DueDate,
        ISNULL(I.PayableAmount, 0) AS PayableAmount,
        ISNULL(I.PaidAmount, 0) AS InstallmentPaid,
        ISNULL(I.BalanceAmount, 0) AS InstallmentBalance,
        I.Status AS InstallmentStatus,
        CASE
            WHEN I.DueDate < CAST(GETDATE() AS DATE) AND ISNULL(I.BalanceAmount, 0) > 0
                 AND ISNULL(I.Status, '') NOT IN ('Paid', 'Cancelled', 'ConfigPending') THEN 1
            ELSE 0
        END AS IsOverdue
    FROM dbo.Tbl_StudentFeeAssignment A
    INNER JOIN dbo.Tbl_StudentFeeInstallment I
            ON I.StudentFeeAssignmentId = A.StudentFeeAssignmentId
    LEFT JOIN dbo.Tbl_CourseMaster CM ON CM.CourseId = A.CourseId
    WHERE A.BranchId = @BranchId
      AND (@OrgId = 0 OR A.OrganizationId = @OrgId)
      AND ISNULL(A.Status, '') <> 'Closed'
      AND (
          A.StudentId = @StudentRegNo
          OR TRY_CAST(A.StudentRegNo AS BIGINT) = @StudentRegNo
          OR A.StudentRegNo LIKE '%' + CAST(@StudentRegNo AS NVARCHAR(30))
      )
    ORDER BY TRY_CAST(I.DueDate AS DATE), I.SortOrder, I.StudentFeeInstallmentId;
END
GO

CREATE OR ALTER PROCEDURE dbo.USP_ChatBot_StudentFeeOverdue
(
    @StudentRegNo BIGINT,
    @BranchId INT,
    @OrgId INT = 0
)
AS
BEGIN
    SET NOCOUNT ON;

    SELECT TOP 30
        A.StudentName,
        TRY_CAST(A.StudentRegNo AS BIGINT) AS StudentRegNo,
        ISNULL(CM.CourseName, '') AS CourseName,
        I.FeeHeadName,
        CONVERT(VARCHAR(10), I.DueDate, 120) AS DueDate,
        ISNULL(I.BalanceAmount, 0) AS OverdueAmount,
        DATEDIFF(DAY, I.DueDate, CAST(GETDATE() AS DATE)) AS DaysOverdue
    FROM dbo.Tbl_StudentFeeInstallment I
    INNER JOIN dbo.Tbl_StudentFeeAssignment A
            ON A.StudentFeeAssignmentId = I.StudentFeeAssignmentId
    LEFT JOIN dbo.Tbl_CourseMaster CM ON CM.CourseId = A.CourseId
    WHERE A.BranchId = @BranchId
      AND (@OrgId = 0 OR A.OrganizationId = @OrgId)
      AND ISNULL(A.Status, '') <> 'Closed'
      AND (
          A.StudentId = @StudentRegNo
          OR TRY_CAST(A.StudentRegNo AS BIGINT) = @StudentRegNo
      )
      AND I.DueDate < CAST(GETDATE() AS DATE)
      AND ISNULL(I.BalanceAmount, 0) > 0
      AND ISNULL(I.Status, '') NOT IN ('Paid', 'Cancelled', 'ConfigPending')
    ORDER BY I.DueDate;
END
GO

CREATE OR ALTER PROCEDURE dbo.USP_ChatBot_StudentReceiptHistory
(
    @StudentRegNo BIGINT,
    @BranchId INT,
    @OrgId INT = 0
)
AS
BEGIN
    SET NOCOUNT ON;

    SELECT TOP 20
        CONVERT(VARCHAR(20), R.ReceiptDate, 106) AS ReceiptDate,
        R.PaymentMode,
        ISNULL(R.TotalPaidAmount, 0) AS PaidAmount,
        ISNULL(R.DiscountAmount, 0) AS DiscountAmount,
        ISNULL(R.LateFeeAmount, 0) AS LateFeeAmount,
        R.Status,
        CASE
            WHEN LEN(ISNULL(R.ReferenceNo, '')) <= 4 THEN ISNULL(R.ReferenceNo, '')
            ELSE '****' + RIGHT(R.ReferenceNo, 4)
        END AS ReferenceMasked,
        ISNULL(R.ScholarshipName, '') AS ScholarshipName,
        A.StudentName,
        ISNULL(CM.CourseName, '') AS CourseName
    FROM dbo.Tbl_StudentFeeReceipt R
    INNER JOIN dbo.Tbl_StudentFeeAssignment A
            ON A.StudentFeeAssignmentId = R.StudentFeeAssignmentId
    LEFT JOIN dbo.Tbl_CourseMaster CM ON CM.CourseId = A.CourseId
    WHERE R.BranchId = @BranchId
      AND (@OrgId = 0 OR R.OrganizationId = @OrgId)
      AND (
          A.StudentId = @StudentRegNo
          OR TRY_CAST(A.StudentRegNo AS BIGINT) = @StudentRegNo
      )
      AND ISNULL(R.Status, '') NOT IN ('Rollback', 'Cancelled')
    ORDER BY R.ReceiptDate DESC, R.StudentFeeReceiptId DESC;
END
GO

CREATE OR ALTER PROCEDURE dbo.USP_ChatBot_FeeBranchSnapshot
(
    @BranchId INT,
    @OrgId INT = 0,
    @CourseId INT = 0
)
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @Today DATE = CAST(GETDATE() AS DATE);

    SELECT
        ISNULL((
            SELECT SUM(R.TotalPaidAmount)
            FROM dbo.Tbl_StudentFeeReceipt R
            INNER JOIN dbo.Tbl_StudentFeeAssignment A ON A.StudentFeeAssignmentId = R.StudentFeeAssignmentId
            WHERE R.BranchId = @BranchId
              AND (@OrgId = 0 OR R.OrganizationId = @OrgId)
              AND (@CourseId = 0 OR A.CourseId = @CourseId)
              AND CAST(R.ReceiptDate AS DATE) = @Today
              AND R.Status = 'Paid'
        ), 0) AS TodayCollection,
        ISNULL((
            SELECT SUM(A.BalanceAmount)
            FROM dbo.Tbl_StudentFeeAssignment A
            WHERE A.BranchId = @BranchId
              AND (@OrgId = 0 OR A.OrganizationId = @OrgId)
              AND (@CourseId = 0 OR A.CourseId = @CourseId)
              AND ISNULL(A.Status, '') <> 'Closed'
        ), 0) AS TotalPendingBalance,
        ISNULL((
            SELECT SUM(I.BalanceAmount)
            FROM dbo.Tbl_StudentFeeInstallment I
            INNER JOIN dbo.Tbl_StudentFeeAssignment A ON A.StudentFeeAssignmentId = I.StudentFeeAssignmentId
            WHERE A.BranchId = @BranchId
              AND (@OrgId = 0 OR A.OrganizationId = @OrgId)
              AND (@CourseId = 0 OR A.CourseId = @CourseId)
              AND I.DueDate < @Today
              AND ISNULL(I.BalanceAmount, 0) > 0
              AND ISNULL(I.Status, '') NOT IN ('Paid', 'Cancelled', 'ConfigPending')
        ), 0) AS OverdueAmount,
        ISNULL((
            SELECT COUNT(DISTINCT A.StudentId)
            FROM dbo.Tbl_StudentFeeAssignment A
            WHERE A.BranchId = @BranchId
              AND (@OrgId = 0 OR A.OrganizationId = @OrgId)
              AND (@CourseId = 0 OR A.CourseId = @CourseId)
              AND ISNULL(A.Status, '') <> 'Closed'
        ), 0) AS ActiveStudentsWithFee,
        ISNULL((
            SELECT COUNT(DISTINCT A.StudentId)
            FROM dbo.Tbl_StudentFeeInstallment I
            INNER JOIN dbo.Tbl_StudentFeeAssignment A ON A.StudentFeeAssignmentId = I.StudentFeeAssignmentId
            WHERE A.BranchId = @BranchId
              AND (@OrgId = 0 OR A.OrganizationId = @OrgId)
              AND (@CourseId = 0 OR A.CourseId = @CourseId)
              AND I.DueDate < @Today
              AND ISNULL(I.BalanceAmount, 0) > 0
        ), 0) AS OverdueStudentCount;
END
GO

CREATE OR ALTER PROCEDURE dbo.USP_ChatBot_PendingFeeStudents
(
    @BranchId INT,
    @OrgId INT = 0,
    @CourseId INT = 0,
    @BatchId BIGINT = 0,
    @SearchText NVARCHAR(150) = '',
    @PageSize INT = 15
)
AS
BEGIN
    SET NOCOUNT ON;
    IF @PageSize IS NULL OR @PageSize <= 0 SET @PageSize = 15;
    IF @PageSize > 25 SET @PageSize = 25;
    SET @SearchText = LTRIM(RTRIM(ISNULL(@SearchText, '')));

    SELECT TOP (@PageSize)
        TRY_CAST(A.StudentRegNo AS BIGINT) AS StudentRegNo,
        A.StudentName,
        ISNULL(CM.CourseName, '') AS CourseName,
        ISNULL(A.BatchName, CB.BatchName) AS BatchName,
        ISNULL(A.GrandTotal, 0) AS GrandTotal,
        ISNULL(A.PaidAmount, 0) AS PaidAmount,
        ISNULL(A.BalanceAmount, 0) AS BalanceAmount,
        CAST(CASE WHEN ISNULL(A.GrandTotal, 0) <= 0 THEN 0
             ELSE (ISNULL(A.BalanceAmount, 0) * 100.0 / A.GrandTotal) END AS DECIMAL(9,2)) AS PendingPercent
    FROM dbo.Tbl_StudentFeeAssignment A
    LEFT JOIN dbo.Tbl_CourseMaster CM ON CM.CourseId = A.CourseId
    LEFT JOIN dbo.Tbl_CourseBatch CB ON CB.BatchId = A.BatchId
    WHERE A.BranchId = @BranchId
      AND (@OrgId = 0 OR A.OrganizationId = @OrgId)
      AND (@CourseId = 0 OR A.CourseId = @CourseId)
      AND (@BatchId = 0 OR A.BatchId = @BatchId)
      AND ISNULL(A.Status, '') <> 'Closed'
      AND ISNULL(A.BalanceAmount, 0) > 0
      AND (
          @SearchText = ''
          OR A.StudentName LIKE '%' + @SearchText + '%'
          OR A.StudentRegNo LIKE '%' + @SearchText + '%'
      )
    ORDER BY A.BalanceAmount DESC, A.StudentName;
END
GO
