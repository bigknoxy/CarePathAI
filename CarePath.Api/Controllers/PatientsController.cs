using Microsoft.AspNetCore.Mvc;
using CarePath.Domain.DTOs;

namespace CarePath.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class PatientsController : ControllerBase
{
    private static readonly List<PatientDto> _patients = new()
    {
        new PatientDto 
        { 
            Id = 1, 
            FirstName = "John", 
            LastName = "Doe", 
            DateOfBirth = "1980-01-15", 
            MedicalRecordNumber = "MRN001" 
        },
        new PatientDto 
        { 
            Id = 2, 
            FirstName = "Jane", 
            LastName = "Smith", 
            DateOfBirth = "1992-06-23", 
            MedicalRecordNumber = "MRN002" 
        }
    };

    [HttpGet]
    public ActionResult<IEnumerable<PatientDto>> Get()
    {
        return Ok(_patients);
    }
}