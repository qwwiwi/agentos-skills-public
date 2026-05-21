#!/usr/bin/env bash
exec "$(dirname "$0")/merge-reviews.sh" "${1:?run dir required}" audit
