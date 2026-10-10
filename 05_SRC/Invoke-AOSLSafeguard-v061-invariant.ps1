param(
    [Parameter(Mandatory=$true)][string]$CasesPath,
    [Parameter(Mandatory=$true)][string]$JudgmentsPath,
    [Parameter(Mandatory=$true)][string]$OutputPath
)

$ErrorActionPreference = "Stop"

foreach ($path in @($CasesPath, $JudgmentsPath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Missing input: $path"
    }
}

if (Test-Path -LiteralPath $OutputPath) {
    throw "Refusing to overwrite: $OutputPath"
}

$cases = @(Import-Csv -LiteralPath $CasesPath)
$judgments = @(Import-Csv -LiteralPath $JudgmentsPath)

if ($cases.Count -eq 0) {
    throw "Empty case dataset."
}

foreach ($column in @("case_id","evidence","response")) {
    if ($column -notin $cases[0].PSObject.Properties.Name) {
        throw "Missing case column: $column"
    }
}

if ($judgments.Count -gt 0) {
    foreach ($column in @("CaseID","Focus","Actual")) {
        if ($column -notin $judgments[0].PSObject.Properties.Name) {
            throw "Missing judgment column: $column"
        }
    }
}

$ids = @($cases | ForEach-Object { $_.case_id })

if (@($ids | Select-Object -Unique).Count -ne $cases.Count) {
    throw "Duplicate case IDs."
}

if (@($ids | Where-Object { [string]::IsNullOrWhiteSpace($_) }).Count -gt 0) {
    throw "Empty case ID."
}

$duplicateJudgments = @(
    $judgments |
    Where-Object { $_.Focus -eq "C1" } |
    Group-Object CaseID |
    Where-Object Count -gt 1
)

if ($duplicateJudgments.Count -gt 0) {
    throw "Duplicate C1 model judgments."
}

# Frozen v0.4.1 strict parsing rules.
$evidencePattern = '\ARevenue was CHF (?<before>[0-9]+(?:\.[0-9]+)?) before and CHF (?<after>[0-9]+(?:\.[0-9]+)?) after\.\z'
$responsePattern = '\ARevenue increased by CHF (?<claimed>[0-9]+(?:\.[0-9]+)?)\.\z'

$culture = [System.Globalization.CultureInfo]::InvariantCulture

$results = foreach ($case in $cases) {

    $status = "NOT_CHECKED"
    $reason = "Outside strict supported format"
    $computed = $null
    $claimed = $null
    $ruleC1 = $null
    $modelC1 = $null
    $disagreement = $false

    $em = [regex]::Match($case.evidence, $evidencePattern)
    $rm = [regex]::Match($case.response, $responsePattern)

    if ($em.Success -and $rm.Success) {

        $before = [decimal]0
        $after = [decimal]0
        $parsedClaim = [decimal]0

        $numericValid = (
            [decimal]::TryParse(
                $em.Groups["before"].Value, [System.Globalization.NumberStyles]::Number, $culture, [ref]$before
            ) -and
            [decimal]::TryParse(
                $em.Groups["after"].Value, [System.Globalization.NumberStyles]::Number, $culture, [ref]$after
            ) -and
            [decimal]::TryParse(
                $rm.Groups["claimed"].Value, [System.Globalization.NumberStyles]::Number, $culture, [ref]$parsedClaim
            )
        )

        if ($numericValid) {
            try {
                $computed = [decimal]::Subtract($after, $before)
            }
            catch [System.OverflowException] {
                $numericValid = $false
                $computed = $null
            }
        }

        if ($numericValid) {

            $claimed = $parsedClaim

            if ($computed -gt 0) {

                $ruleC1 = if ($claimed -eq $computed) { 0 } else { 1 }

                $matching = @(
                    $judgments | Where-Object {
                        $_.CaseID -eq $case.case_id -and
                        $_.Focus -eq "C1"
                    }
                )

                if ($matching.Count -eq 1) {

                    if ($matching[0].Actual -notin @("0","1")) {
                        throw "Invalid original C1 judgment for $($case.case_id)"
                    }

                    $modelC1 = [int]$matching[0].Actual
                    $disagreement = ($ruleC1 -ne $modelC1)

                    $status = if ($disagreement) {
                        "DISAGREEMENT"
                    } else {
                        "CHECKED"
                    }

                    $reason = "Arithmetic compared with original model C1"
                }
                else {
                    $status = "CHECKED_NO_MODEL_COMPARISON"
                    $reason = "Arithmetic checked; no C1 judgment supplied"
                }
            }
            else {
                $reason = "Non-positive increase outside supported rule"
            }
        }
        else {
            $computed = $null
            $claimed = $null
            $reason = "Numeric value outside supported decimal range"
        }
    }

    [pscustomobject]@{
        CaseID = $case.case_id
        Status = $status
        ComputedDifference = $computed
        ClaimedDifference = $claimed
        RuleBasedC1 = $ruleC1
        OriginalModelC1 = $modelC1
        Disagreement = $disagreement
        Reason = $reason
    }
}

$results |
    Export-Csv -LiteralPath $OutputPath -NoTypeInformation -Encoding UTF8

[pscustomobject]@{
    Total = $results.Count
    Disagreements = @($results | Where-Object Status -eq "DISAGREEMENT").Count
    Agreements = @($results | Where-Object Status -eq "CHECKED").Count
    NotChecked = @($results | Where-Object Status -eq "NOT_CHECKED").Count
    NoModelComparison = @($results | Where-Object Status -eq "CHECKED_NO_MODEL_COMPARISON").Count
    CasesSHA256 = (Get-FileHash $CasesPath -Algorithm SHA256).Hash
    JudgmentsSHA256 = (Get-FileHash $JudgmentsPath -Algorithm SHA256).Hash
    OutputSHA256 = (Get-FileHash $OutputPath -Algorithm SHA256).Hash
}
