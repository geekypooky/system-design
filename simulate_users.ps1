$BaseUrl = "http://localhost:8080"
$TotalUsers = 10
$ProductId = "X"

Write-Host "`n=== Salestorm 10-User Simulation ===" -ForegroundColor Cyan
Write-Host "Starting $TotalUsers concurrent user flows...`n" -ForegroundColor Gray

$results = @()

$jobs = 1..$TotalUsers | ForEach-Object {
    $userId = $_
    Start-Job -ScriptBlock {
        param($baseUrl, $userId, $productId)

        $customerId = "sim-user-$userId"
        $result = [PSCustomObject]@{
            User            = "User $userId"
            CustomerId      = $customerId
            ReservationId   = $null
            ReservationStatus = $null
            PaymentId       = $null
            PaymentStatus   = $null
            Error           = $null
        }

        try {
            # Step 1: Create Reservation
            $resBody = @{ customer_id = $customerId; product_id = $productId; quantity = 1 } | ConvertTo-Json
            $resResponse = Invoke-RestMethod -Uri "$baseUrl/v1/reservations" `
                -Method POST -ContentType "application/json" -Body $resBody

            $result.ReservationId     = $resResponse.reservation_id
            $result.ReservationStatus = $resResponse.status

            # Step 2: Checkout
            $checkBody = @{ reservation_id = $resResponse.reservation_id; amount = 99.99 } | ConvertTo-Json
            $payResponse = Invoke-RestMethod -Uri "$baseUrl/v1/checkout" `
                -Method POST -ContentType "application/json" -Body $checkBody

            $result.PaymentId     = $payResponse.payment_id
            $result.PaymentStatus = $payResponse.status

        } catch {
            $result.Error = $_.Exception.Message
        }

        return $result

    } -ArgumentList $BaseUrl, $userId, $ProductId
}

# Wait for all jobs
$jobs | Wait-Job | Out-Null

# Collect results
foreach ($job in $jobs) {
    $results += Receive-Job -Job $job
}

# Clean up jobs
$jobs | Remove-Job

# Display results table
Write-Host "`n--- Results ---`n" -ForegroundColor Yellow
$results | Format-Table -AutoSize User, ReservationStatus, ReservationId, PaymentStatus, PaymentId, Error

# Summary
$success  = ($results | Where-Object { $_.PaymentStatus -eq "SUCCESS" }).Count
$failed   = ($results | Where-Object { $_.Error -ne $null }).Count
$existing = ($results | Where-Object { $_.ReservationStatus -eq "existing" }).Count

Write-Host "--- Summary ---" -ForegroundColor Yellow
Write-Host "  Total Users     : $TotalUsers"
Write-Host "  Payments OK     : $success"   -ForegroundColor Green
Write-Host "  Errors          : $failed"    -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })
Write-Host "  Existing Resv.  : $existing"  -ForegroundColor Cyan
Write-Host ""
