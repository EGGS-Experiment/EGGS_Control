@echo off
setlocal EnableDelayedExpansion

for /r %%x in (.) do (
    cd %%x

    for /d %%i in (*.dir) do (

        for /f "tokens=1,2 delims=." %%a in ("%%i") do (
            ren "%%a.dir" "%%a"
        )

    )
)

endlocal
