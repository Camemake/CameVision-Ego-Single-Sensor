#!/bin/sh
(logread 2>/dev/null || true) | grep -iE 'advert|parse_|Local name|Failed' | tail -15
echo WHY
