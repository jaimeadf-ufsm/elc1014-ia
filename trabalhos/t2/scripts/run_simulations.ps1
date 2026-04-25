# PowerShell script to run simulations with incrementing index
# Press Ctrl+C to stop

$index = 18

while ($true) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "Starting iteration $index" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    # Command 1: classical training
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Running command 1 (classical)..." -ForegroundColor Yellow
    try {
        & python .\src\main.py simulate classical randomized_mcts_25000_vs_mcts_25000 -n 50 -w 12 -o "simulations/classical/training/randomized_mcts_25000_vs_mcts_25000_$index.pkl"
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Command 1 completed successfully" -ForegroundColor Green
    }
    catch {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Command 1 failed with error: $_" -ForegroundColor Red
    }
    
    # Command 2: wrap_around training
    # Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Running command 2 (wrap_around)..." -ForegroundColor Yellow
    # try {
    #     & python .\src\main.py simulate wrap_around randomized_mcts_10000_vs_mcts_10000 -n 50 -w 14 -o "simulations/wrap_around/training/randomized_mcts_10000_vs_mcts_10000_$index.pkl"
    #     Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Command 2 completed successfully" -ForegroundColor Green
    # }
    # catch {
    #     Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Command 2 failed with error: $_" -ForegroundColor Red
    # }
    
    $index++
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Iteration complete. Press Ctrl+C to stop or wait for next iteration..." -ForegroundColor Cyan
    Write-Host ""
}
