FROM node:19-alpine
RUN npm i @tuyapi/cli -g 
RUN apk add --no-cache python3 tzdata
COPY cronjobs /etc/crontabs/root
COPY main.py /
CMD ["crond", "-f", "-d", "8"]