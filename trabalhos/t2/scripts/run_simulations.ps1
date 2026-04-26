# ============================================================
# PowerShell Script to Run Othello Simulations
# ============================================================
# Configuration: Edit these variables to customize the simulation runs

# Evaluators to test
$evaluators = @(
    "cee1",
    "cste1",
    "cwte1"
)

# Depths to test
$depths = @(1, 2, 3, 4, 5, 6)

# Iterations for MCTS
$iterations = @(2500, 5000, 7500, 10000)

# Game variants to test
$variants = @("classical")

# Number of matches per simulation
$numMatches = 7

# Number of worker threads
$numWorkers = 14

# Individual presets to run (if empty, will use the generated list from evaluators/depths/iterations)
# Example: $individualPresets = @("randomized_mcts_1000_vs_mcts_1000", "randomized_mcts_10000_vs_mcts_10000")
$individualPresets = @()

# Number of batches to run (each batch will append _1, _2, etc. to filename)
$numBatches = 10

# ============================================================
# Script Logic (Do not modify below)
# ============================================================

function Generate-PresetName {
    param(
        [string]$evaluatorName,
        [int]$depth,
        [int]$iterations
    )
    return "standard_minimax_$($evaluatorName.ToLower())_$depth`_vs_mcts_$($iterations)"
}

function Generate-Presets {
    $presets = @()
    
    if ($individualPresets.Count -eq 0) {
        # Generate from evaluators × depths × iterations
        foreach ($iteration in $iterations) {
            foreach ($depth in $depths) {
                foreach ($evaluator in $evaluators) {
                    $preset = Generate-PresetName $evaluator $depth $iteration
                    $presets += $preset
                }
            }
        }
    } else {
        $presets = $individualPresets
    }
    
    return $presets
}

function Get-OutputPath {
    param(
        [string]$variant,
        [string]$preset,
        [int]$batch
    )
    return "simulations/$variant/testing/$preset`_$batch.pkl"
}

function Run-Simulation {
    param(
        [string]$variant,
        [string]$preset,
        [string]$outputPath
    )
    
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    
    # Check if output file already exists
    if (Test-Path $outputPath) {
        Write-Host "[$timestamp] SKIP - File exists: $outputPath" -ForegroundColor Yellow
        return $true
    }
    
    # Create output directory if it doesn't exist
    $outputDir = Split-Path $outputPath
    if (-not (Test-Path $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    }
    
    # Run the simulation command
    Write-Host "[$timestamp] Running: python .\src\main.py simulate $variant $preset -n $numMatches -w $numWorkers -o `"$outputPath`"" -ForegroundColor Cyan
    
    try {
        & python .\src\main.py simulate $variant $preset -n $numMatches -w $numWorkers -o $outputPath
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[$timestamp] SUCCESS: $variant / $preset" -ForegroundColor Green
            return $true
        } else {
            Write-Host "[$timestamp] FAILED (exit code $LASTEXITCODE): $variant / $preset" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "[$timestamp] ERROR: $_ - $variant / $preset" -ForegroundColor Red
        return $false
    }
}

function Show-PresetConfirmation {
    param(
        [array]$presets,
        [array]$variants
    )
    
    Write-Host ""
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host "SIMULATION CONFIGURATION" -ForegroundColor Cyan
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Variants: $($variants -join ', ')" -ForegroundColor White
    Write-Host "Presets: $($presets.Count)" -ForegroundColor White
    Write-Host "Matches per simulation: $numMatches" -ForegroundColor White
    Write-Host "Worker threads: $numWorkers" -ForegroundColor White
    Write-Host ""
    Write-Host "Presets to execute:" -ForegroundColor Cyan
    for ($i = 0; $i -lt $presets.Count; $i++) {
        Write-Host "  $($i + 1). $($presets[$i])" -ForegroundColor White
    }
    Write-Host ""
    Write-Host "Total simulations: $($variants.Count * $presets.Count)" -ForegroundColor Yellow
    Write-Host ""
    
    $response = Read-Host "Continue with these simulations? (yes/no)"
    return $response -eq "yes" -or $response -eq "y"
}

# Main execution
Write-Host ""
Write-Host "Othello Simulation Runner" -ForegroundColor Cyan
Write-Host ""

# Generate presets
$presets = Generate-Presets
Write-Host "Generated $($presets.Count) preset(s)" -ForegroundColor Gray

# Show confirmation
if (-not (Show-PresetConfirmation $presets $variants)) {
    Write-Host "Cancelled by user." -ForegroundColor Yellow
    exit 0
}

# Run simulations for each batch
$totalSimulations = $variants.Count * $presets.Count * $numBatches
$totalCompletedSimulations = 0
$totalSkippedSimulations = 0
$totalFailedSimulations = 0

Write-Host "Starting $numBatches batch(es) of simulations..." -ForegroundColor Green
Write-Host ""

for ($batchNum = 1; $batchNum -le $numBatches; $batchNum++) {
    Write-Host "=""=""=""=""=""=""=""=""=""=""=""" -ForegroundColor Cyan
    Write-Host "BATCH $batchNum / $numBatches" -ForegroundColor Cyan
    Write-Host "=""=""=""=""=""=""=""=""=""=""=""" -ForegroundColor Cyan
    Write-Host ""
    
    $completedSimulations = 0
    $skippedSimulations = 0
    $failedSimulations = 0
    
    foreach ($variant in $variants) {
        foreach ($preset in $presets) {
            $completedSimulations++
            $totalCompletedSimulations++
            $outputPath = Get-OutputPath $variant $preset $batchNum
            
            Write-Host "[$totalCompletedSimulations/$totalSimulations]" -ForegroundColor Magenta -NoNewline
            Write-Host " "
            
            $success = Run-Simulation $variant $preset $outputPath
            
            if (-not $success) {
                if (Test-Path $outputPath) {
                    $skippedSimulations++
                    $totalSkippedSimulations++
                } else {
                    $failedSimulations++
                    $totalFailedSimulations++
                }
            }
            
            Write-Host ""
        }
    }
    
    Write-Host "Batch $batchNum Summary:" -ForegroundColor Yellow
    Write-Host "  Completed: $($completedSimulations - $skippedSimulations - $failedSimulations)" -ForegroundColor Green
    Write-Host "  Skipped: $skippedSimulations" -ForegroundColor Yellow
    Write-Host "  Failed: $failedSimulations" -ForegroundColor Red
    Write-Host ""
}

# Summary
Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "OVERALL SUMMARY" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "Total simulations: $totalSimulations" -ForegroundColor White
Write-Host "Completed: $($totalSimulations - $totalSkippedSimulations - $totalFailedSimulations)" -ForegroundColor Green
Write-Host "Skipped (already existed): $totalSkippedSimulations" -ForegroundColor Yellow
Write-Host "Failed: $totalFailedSimulations" -ForegroundColor Red
Write-Host ""

if ($totalFailedSimulations -eq 0) {
    Write-Host "All batches completed successfully!" -ForegroundColor Green
} else {
    Write-Host "Some simulations failed. Check the output above for details." -ForegroundColor Yellow
}
