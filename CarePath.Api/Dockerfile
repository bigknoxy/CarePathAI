# Multi-stage build for CarePath.Api
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# Copy csproj and restore dependencies
COPY ["CarePath.Api/CarePath.Api.csproj", "CarePath.Api/"]
COPY ["CarePath.Domain/CarePath.Domain.csproj", "CarePath.Domain/"]
RUN dotnet restore "CarePath.Api/CarePath.Api.csproj"

# Copy the rest of the source files
COPY . .
WORKDIR "/src/CarePath.Api"
RUN dotnet build "CarePath.Api.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "CarePath.Api.csproj" -c Release -o /app/publish /p:UseAppHost=false

# Runtime stage
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS final
WORKDIR /app
COPY --from=publish /app/publish .
EXPOSE 5000
ENV ASPNETCORE_URLS=http://+:5000
ENV ASPNETCORE_ENVIRONMENT=Production
ENTRYPOINT ["dotnet", "CarePath.Api.dll"]