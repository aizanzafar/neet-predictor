$bases = @("https://cetonline.karnataka.gov.in/keawebentry456/ugneet22/","https://cetonline.karnataka.gov.in/keawebentry456/ugneet2022/")
$filenames = @("ebrochure.pdf","ebrochureenglish.pdf","bds_notificationenglish.pdf","bds_notificationkannada.pdf","INSTRUTIONSenglish.pdf","INSTRUTIONSkannada.pdf","mopup_dentalenglish.pdf","Neet_govnotificationenglish.pdf","Neet_govnotificationkannada.pdf","aiq_joined_kea_candidatesenglish.pdf","aiq_joined_kea_candidateskannada.pdf","first_round_seat_allotment_scheduleenglish.pdf","first_round_seat_allotment_schedulekannada.pdf","press_noteenglish.pdf","pressnoteUGNEET2022english.pdf","mcc_notificationenglish.pdf","mcc_notificationkannada.pdf","flow_chart_mopup_roundenglish.pdf","POST_SEAT_ALLOTMENT_PROCEDURE_FORUGNEET2022english.pdf","POST_SEAT_ALLOTMENT_PROCEDURE_FORUGNEET2022kannada.pdf","ugneet_mopup_scheduleenglish.pdf","mopup_r2_dental_scheduleenglish.pdf","additional instructions NEETenglish.pdf","rank wise schedule mop up - stagesenglish.pdf","UGNEET_ALLOT_2022_MEDICAL_R1english.pdf","UGNEET_ALLOT_2022_MEDICAL_R1kannada.pdf","UGNEET_ALLOT_2022_MEDICAL_R2english.pdf","UGNEET_ALLOT_2021_MEDICAL_R1english.pdf","UGNEET_ALLOT_2021_MEDICAL_R2english.pdf","seatmatrixenglish.pdf","seatmatrixkannada.pdf","SeatMatrix.pdf","feeenglish.pdf","fees.pdf","feesstructureenglish.pdf","cutoffenglish.pdf","allotmentlistenglish.pdf","secondround_mopup_dental_scheduleenglish.pdf","bds_instructionskannada.pdf","ugneetprovisional_list_instructionkannada.pdf")
foreach ($base in $bases) {
    Write-Output "=== Testing: $base ==="
    $foundCount = 0
    foreach ($file in $filenames) {
        $url = $base + $file
        try {
            $response = Invoke-WebRequest -Uri $url -Method Head -TimeoutSec 8 -UseBasicParsing -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                $cl = $response.Headers['Content-Length']
                Write-Output "  FOUND: $file ($cl bytes)"
                $foundCount++
            }
        } catch { }
    }
    Write-Output "  Total found: $foundCount / $($filenames.Count)"
}
Write-Output ""
Write-Output "=== Testing 2024-style allotment URLs ==="
$allotUrls = @("https://cetonline.karnataka.gov.in/keawebentry456/ugneet22/UGNEET_ALLOT_2021_MEDICAL_R1_provenglish.pdf","https://cetonline.karnataka.gov.in/keawebentry456/ugneet22/UGNEET_ALLOT_2021_MEDICAL_R1_provkannada.pdf","https://cetonline.karnataka.gov.in/keawebentry456/ugneet22/UGNEET_ALLOT_2022_MEDICAL_R1_provenglish.pdf","https://cetonline.karnataka.gov.in/keawebentry456/ugneet22/UGNEET_ALLOT_2022_MEDICAL_R1_provkannada.pdf","https://cetonline.karnataka.gov.in/keawebentry456/ugneet24/UGNEET_ALLOT_2024_MEDICAL_R1_provenglish.pdf","https://cetonline.karnataka.gov.in/keawebentry456/ugneet24/UGNEET_ALLOT_2024_MEDICAL_R1_provkannada.pdf","https://cetonline.karnataka.gov.in/keawebentry456/ugneet24/UGNEET_ALLOT_2024_MEDICAL_R2_provenglish.pdf","https://cetonline.karnataka.gov.in/keawebentry456/ugneet24/UGNEET_ALLOT_2024_MEDICAL_R2_provkannada.pdf")
foreach ($url in $allotUrls) {
    try {
        $response = Invoke-WebRequest -Uri $url -Method Head -TimeoutSec 8 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $cl = $response.Headers['Content-Length']
            Write-Output "  FOUND: $url ($cl bytes)"
        }
    } catch {
        $status = $null
        if ($_.Exception.Response) { $status = [int]$_.Exception.Response.StatusCode }
        if ($status -and $status -ne 404) {
            Write-Output "  STATUS $status : $url"
        }
    }
}
