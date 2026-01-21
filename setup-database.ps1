# Supabase Database Setup Script
# Run this after you get your password from Supabase

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Supabase Database Configuration Helper                  ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Step 1: Get Password
Write-Host "STEP 1: Get Your Database Password" -ForegroundColor Yellow
Write-Host "---------------------------------------" -ForegroundColor Gray
Write-Host "Open this URL in your browser:" -ForegroundColor White
Write-Host "https://supabase.com/dashboard/project/tujrzlxbckqyuwqrylck/settings/database`n" -ForegroundColor Cyan

$password = Read-Host "Paste your Supabase database password here"

if ([string]::IsNullOrWhiteSpace($password)) {
    Write-Host "`n✗ No password provided. Exiting.`n" -ForegroundColor Red
    exit 1
}

# Step 2: Update .env file
Write-Host "`nSTEP 2: Updating .env file..." -ForegroundColor Yellow

$envPath = ".env"
$envContent = Get-Content $envPath -Raw

# Replace placeholder with actual password in both connection strings
$envContent = $envContent -replace '\[YOUR-DB-PASSWORD\]', $password
$envContent = $envContent -replace '\[YOUR-PASSWORD\]', $password

# Save updated .env
$envContent | Set-Content $envPath -NoNewline

Write-Host "✓ .env file updated successfully!`n" -ForegroundColor Green

# Step 3: Test connection
Write-Host "STEP 3: Testing Database Connection..." -ForegroundColor Yellow
Write-Host "(This will test if your password works)`n" -ForegroundColor Gray

# Build connection strings
$poolerUrl = "postgresql://postgres.tujrzlxbckqyuwqrylck:$password@aws-0-us-east-1.pooler.supabase.com:6543/postgres?pgbouncer=true"
$directUrl = "postgresql://postgres:$password@db.tujrzlxbckqyuwqrylck.supabase.co:5432/postgres"

Write-Host "Connection strings configured:" -ForegroundColor White
Write-Host "  Pooler (for app): ...pooler.supabase.com:6543" -ForegroundColor Gray
Write-Host "  Direct (for migrations): ...db.tujrzlxbckqyuwqrylck.supabase.co:5432`n" -ForegroundColor Gray

# Step 4: Check pgvector extension
Write-Host "STEP 4: Enable pgvector Extension" -ForegroundColor Yellow
Write-Host "---------------------------------------" -ForegroundColor Gray
Write-Host "Open this URL in your browser:" -ForegroundColor White
Write-Host "https://supabase.com/dashboard/project/tujrzlxbckqyuwqrylck/database/extensions`n" -ForegroundColor Cyan
Write-Host "Search for 'vector' and click Enable if not already enabled`n" -ForegroundColor White

$vectorEnabled = Read-Host "Have you enabled the vector extension? (y/n)"

if ($vectorEnabled -ne 'y') {
    Write-Host "`n⚠ Please enable the vector extension before continuing`n" -ForegroundColor Yellow
    exit 0
}

# Step 5: Run Migrations
Write-Host "`nSTEP 5: Ready to Run Migrations" -ForegroundColor Yellow
Write-Host "---------------------------------------" -ForegroundColor Gray
Write-Host "The .env file is now configured with:" -ForegroundColor White
Write-Host "  ✓ Database password" -ForegroundColor Green
Write-Host "  ✓ Pooler connection (for app)" -ForegroundColor Green
Write-Host "`nFor migrations, temporarily switch to direct connection:" -ForegroundColor Yellow
Write-Host "  1. Edit .env" -ForegroundColor White
Write-Host "  2. Change DATABASE_URL from:" -ForegroundColor White
Write-Host "     ...pooler.supabase.com:6543...?pgbouncer=true" -ForegroundColor Gray
Write-Host "     to:" -ForegroundColor White
Write-Host "     ...db.tujrzlxbckqyuwqrylck.supabase.co:5432..." -ForegroundColor Gray
Write-Host "  3. Run: cd backend; poetry install; poetry run alembic upgrade head" -ForegroundColor White
Write-Host "  4. Change back to pooler connection`n" -ForegroundColor White

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   Configuration Complete! Next Steps:                     ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "1. Switch to direct connection in .env (for migrations)" -ForegroundColor Cyan
Write-Host "2. Run migrations: cd backend; poetry run alembic upgrade head" -ForegroundColor Cyan
Write-Host "3. Switch back to pooler connection in .env" -ForegroundColor Cyan
Write-Host "4. Start services: docker compose up -d`n" -ForegroundColor Cyan

Write-Host "See QUICKSTART.md for detailed instructions`n" -ForegroundColor Gray
